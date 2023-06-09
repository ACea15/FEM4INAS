"""Functions to define the geometry of load-paths."""
import pandas as pd
import jax.numpy as jnp
import numpy as np
from multipledispatch import dispatch
import pathlib
from typing import Sequence, Any
from fem4inas.utils import flatten_list
from collections.abc import Iterable

def find_fem(folder, Ka_name, Ma_name, grid):

    #TODO: add assertions
    if folder is not None:        
        Ka_path = list(pathlib.Path(folder).glob(f"*{Ka_name}"))[0]
        Ma_path = list(pathlib.Path(folder).glob(f"*{Ma_name}"))[0]
        if isinstance(grid, str):
            grid_path = list(pathlib.Path(folder).glob(f"*{grid}*"))[0]
        else:
            grid_path = grid
    else:
        Ka_path = Ka_name
        Ma_path = Ma_name
        grid_path = grid
    return Ka_path, Ma_path, grid_path

def list2dict(obj: list | dict):

    if isinstance(obj, list):
        out = dict()
        for i, v in enumerate(obj):
            out[str(i)] = v
    elif isinstance(obj, dict):
        out = obj
    return out

def build_grid(grid: str | jnp.ndarray | pd.DataFrame | None,
               X: jnp.ndarray | None,
               fe_order: list[int] | jnp.ndarray | None,
               fe_order_start: int,
               component_vect: list[str] | None) -> (pd.DataFrame,
                                                     jnp.ndarray,
                                                     np.ndarray,
                                                     list[str]):
    if grid is None:
        assert X is not None, "X needs to be provided \
        when no grid file is given"
        assert fe_order is not None, "fe_order needs to be provided \
        when no grid file is given"
        assert component_vect is not None, "component_vect needs to be \
        provided when no grid file is given"
        df_grid = pd.DataFrame(dict(x1=X[:, 0], x2=X[:, 1], x3=X[:, 2],
                                    fe_order=fe_order, component=component_vect))
    elif isinstance(grid, (str, pathlib.Path)):

        df_grid = pd.read_csv(grid, comment="#", sep=" ",
                              names=['x1', 'x2', 'x3', 'fe_order', 'component'])
        
    elif isinstance(grid, jnp.ndarray):
        df_grid = pd.DataFrame(dict(x1=grid[:, 0], x2=grid[:, 1], x3=grid[:, 2],
                                    fe_order=grid[:, 3], component=grid[:, 4]))
    
    elif isinstance(grid, pd.DataFrame):
        df_grid = grid

    if not isinstance(X, jnp.ndarray):
        X = jnp.array(df_grid.to_numpy()[:,:3].astype('float'))
    if not isinstance(fe_order, jnp.ndarray):
        fe_order = df_grid.to_numpy()[:,3:4].astype('int').flatten()
        fe_order -= fe_order_start
    if not isinstance(component_vect, list):
        component_vect = list(df_grid.component.astype('str'))
    df_grid.fe_order -= fe_order_start
    return df_grid, X, fe_order, component_vect

def compute_clamped(fe_order: list[int]) -> (list[int], dict[str: list],
                                             dict[str: list], int):
    clamped_nodes = list()
    freeDoF = dict()
    clampedDoF = dict()
    total_clampedDoF = 0

    for i in fe_order:
        if i < 0:
            fe_node = str(abs(i))
            if len(fe_node) < 6: # clamped node, format = -1 (node 0),
                #-5 (node 4) etc
                clamped_nodes.append(abs(i) - 1)
                freeDoF[clamped_nodes[-1]] = []
                clampedDoF[clamped_nodes[-1]] = list(range(6))
                total_clampedDoF += 6
            elif len(fe_node) > 6: #format = -1010117 with
                # 101011 being clamped/free DoF and abs(-7 + 1)=6
                # being the multibody node
                clamped_nodes.append(int(fe_node[6:]) - 1)
                freeDoF[clamped_nodes[-1]] = [i for i,j in enumerate(fe_node[:6]) if j =='0']
                clampedDoF[clamped_nodes[-1]] = [i for i,j in enumerate(fe_node[:6]) if j =='1']
                total_clampedDoF += len(clampedDoF[clamped_nodes[-1]])
            else: #len(fe_node) == 6, format = -101011, multibody node assummed at 0
                clamped_nodes.append(0)
                # picks the index of free DoF
                freeDoF[0] = [i for i, j in enumerate(fe_node) if j == '0']
                clampedDoF[0] = [i for i, j in enumerate(fe_node) if j == '1']
                total_clampedDoF += len(clampedDoF[0])

    return clamped_nodes, freeDoF, clampedDoF, total_clampedDoF

def compute_component_father(component_connectivity:
                             dict[str:list]) -> (list[str], dict[str:list]):
    """Calculates the father component of each component

    Assuming an outwards flow from the first node, every path in the
    graph is transverse in a particular direction, which defines which
    components follows another

    Parameters
    ----------
    component_connectivity : dict[str:list]
        Connectivity input that sets the components attached to each
        component with the logic above

    Returns
    -------
    dict[str:list]
        Maps the father of each component

    """

    component_names = list(component_connectivity.keys())
    component_father = {ci: None for ci in component_names}
    for k, v in component_connectivity.items():
        if v is not None:
            if isinstance(v, Iterable):
                for vi in v:
                    component_father[str(vi)] = k
            else:
                component_father[str(v)] = k
    return component_names, component_father

@dispatch(list)
def compute_component_nodes(components_range: list[str]) -> dict[str:list]:
    """Links components to their nodes 

    Links the nodes (as indexes of DataFrame or list) to the
    compononent they belong to

    Parameters
    ----------
    components_range : list[str]
        Component list

    Returns
    -------
    dict[str:list]
        Dictionary with component names and the corresponding nodes

    """

    component_nodes = dict()
    for i, ci in enumerate(components_range):
        if ci not in component_nodes.keys():
            component_nodes[ci] = []
        component_nodes[ci].append(i)
    return component_nodes

@dispatch(pd.DataFrame)
def compute_component_nodes(df: pd.DataFrame) -> dict[str:list]:

    component_nodes = dict()
    components = df.component.unique()
    group = df.groupby('component')
    for ci in components:
        component_nodes[ci] = list(group.get_group(ci).index)
    return component_nodes

def compute_prevnode(components_range: Sequence[str],
                     component_nodes: dict[str:list[int]],
                     component_father: dict[str:int]) -> list[int]:

    prevnodes = list()
    j = 0
    current_component = None
    for i, ci in enumerate(components_range):
        if i==0:
            prevnodes.append(0)
            #j += 1
            current_component = ci
        elif ci != current_component: # change in component
            if component_father[ci] is None: # component starting at first node
                prevnodes.append(0)
                current_component = ci
                j = 0
            else:
                prevnodes.append(component_nodes[component_father[ci]][-1])
                current_component = ci
                j = 0
        else:
            prevnodes.append(component_nodes[current_component][j])
            j += 1
    return prevnodes

def compute_component_children(component_name: str,
                               component_connectivity: dict[str:list[str | int]],
                               chain:list = None):

    if chain is None:
        chain = list()
    component_name = str(component_name) # in case components are defined with numbers
    children_components = component_connectivity[component_name]
    if children_components is None or len(children_components) == 0:
        pass
    else:
        chain += [str(cci) for cci in children_components]
        for ci in children_components:
            compute_component_children(ci, component_connectivity, chain)
    return chain

def compute_component_chain(component_names: list[str],
                            component_connectivity: dict[str:list[str | int]]):

    component_chain = {k: compute_component_children(k, component_connectivity)
                       for k in component_names}
    return component_chain

def compute_Maverage(prevnodes: Sequence[int], num_nodes: int) -> jnp.ndarray:

    M = np.eye(num_nodes)
    M[0,0] = 0. # first node should be made 0 since we have Nn - 1 elements:
    # given a structure like *--o--*--o--*, tensors are given in '*', but
    # only the quantity at 'o' is of interest 
    for i in range(1, num_nodes):
        M[prevnodes[i], i] = 1
    M *= 0.5
    return jnp.array(M)

def compute_Mdiff(prevnodes: Sequence[int],
                  num_nodes: int) -> jnp.ndarray:

    M = np.eye(num_nodes)
    M[0,0] = 0.
    for i in range(1, num_nodes):
        M[prevnodes[i], i] = -1
    return jnp.array(M)

def compute_Mfe_order(fe_order: np.ndarray,
                      clamped_nodes,
                      freeDoF,
                      total_clampedDoF,
                      component_nodes,
                      component_chain,
                      num_nodes) -> jnp.ndarray:

    clamped_dofs = 0
    M = np.zeros((6 * num_nodes, 6 * num_nodes - total_clampedDoF))
    for fi, node_index in zip(np.sort(fe_order), np.argsort(fe_order)):
        for di in range(6):
            if node_index in clamped_nodes:
                if di in freeDoF[node_index]:
                    M[6 * node_index + di, 6 * fi + clamped_dofs] = 1.
                    clamped_dofs += 1
                else:
                    continue
            else:
                M[6 * node_index + di, 6 * fi + di + clamped_dofs] = 1.

    return jnp.array(M)

def compute_Mloadpaths(components_range,
                       component_nodes: dict[str:list[int]],
                       component_chain,
                       num_nodes) -> jnp.ndarray:

    M = np.eye(num_nodes)
    M[:, 0] = 1.
    current_component = components_range[0]
    j = 1
    for i in range(1, num_nodes):
        ci = components_range[i]
        if ci != current_component:
            j = 0
            current_component = ci
        ci_nodes = component_nodes[ci]
        ci_children = component_chain[ci]        
        ci_children_nodes = flatten_list([component_nodes[k] for
                                          k in ci_children])
        M[ci_children_nodes, i] = 1.
        M[ci_nodes[j:], i] = 1
        j += 1
    return jnp.array(M)
