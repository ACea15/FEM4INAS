from dataclasses import field
from typing import Sequence, Any
import pandas as pd
import numpy as np
import jax.numpy as jnp
from fem4inas.utils import flatten_list
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import pathlib
from fem4inas.preprocessor.config import Config
import argparse

def dfield(description, **kwargs):

    options = kwargs.pop('options', None)
    default = kwargs.pop('default', 'not_defined')
    init = kwargs.pop('init', True)
    if default != 'not_defined':
        if default is None:
            return field(
                default=default, metadata={"description": description, "options": options},
                init=init, **kwargs
            )
        elif isinstance(default, (str, int, bool, float, tuple)):
            return field(
                default=default, metadata={"description": description, "options": options},
                init=init, **kwargs
            )
        else:
            return field(
                default_factory=(lambda: default),
                metadata={"description": description, "options": options},
                init=init, **kwargs
            )
    else:
        return field(
            metadata={"description": description, "options": options},
            init=init, **kwargs
        )

def initialise_Dclass(data, Dclass):

    if data is None:
        return Dclass()
    elif isinstance(data, dict):
        return Dclass(**data)
    elif isinstance(data, Dclass):
        return data
    else:
        raise TypeError("Wrong input type")

def dump_inputs(data: dict[str:list[Any, str]], ind=0,
                with_comments:bool=True):

    data = CommentedMap(data)
    for k, v in data.items():
        if isinstance(v, dict):
            data[k] = dump_inputs(v, ind=ind+1,
                                  with_comments=with_comments)
        else:
            data[k] = v[0]
            #data.yaml_add_eol_comment(v[1], k)
            if with_comments:
                data.yaml_set_comment_before_after_key(k,
                                                       before=v[1],
                                                       indent=2*ind)
    return data

def load_jnp(path):

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)
    assert path.is_file(), f"{str(path)} is not a file"
    A = jnp.load(path)
    return A

def initialise_config(input_file: str = None,
                      input_dict: dict = None,
                      input_obj: Config = None) -> Config:


    if input_dict is None and input_obj is None:  # inputs given as .yaml file
        parser = argparse.ArgumentParser(prog='FEM4INAS', description=
        """This is the executable of Fininte-Element Models for
        Intrinsic Nonlinear Aeroelastic Simulations.""")
        parser.add_argument('input_file', help='path to the *.yaml input file',
                            type=str, default='')
        if input_file is not None: #running from within python file
            args = parser.parse_args(input_file)
        else: # running from command line
            args = parser.parse_args()
        config = Config.from_file(args.input_file)
    elif input_dict is not None and (input_file is None and
                                     input_obj is None):  # inputs given as dict
        config = Config(input_dict)

    elif input_dict is not None and (input_file is None and
                                     input_obj is None):  #  inputs directly as Config
        config = input_obj
    return config

if __name__ == "__main__":
    comp_conn = dict(c1=['c2','c3', 'c5'], c2=None,
                     c3=['c4'], c4=[], c5=None)
    chain1 = compute_component_children('c1', comp_conn)
    chain2 = compute_component_children('c2', comp_conn)
    chain3 = compute_component_children('c3', comp_conn)
    chain4 = compute_component_children('c4', comp_conn)
    chain5 = compute_component_children('c5', comp_conn)

    components_range = ['c1', 'c1', 'c2', 'c2', 'c4', 'c4', 'c4', 'c3', 'c5', 'c5']
    component_nodes = compute_component_nodes(components_range)
    component_father = compute_component_father(comp_conn)
    prevnodes = compute_prevnode(components_range, component_nodes, component_father)

    comp_conn2 = dict(c1=['c2','c3', 'c5'], c2=None,
                      c3=['c4'], c4=[], c5=None, c6=[])
    chain12 = compute_component_children('c1', comp_conn)
    chain22 = compute_component_children('c2', comp_conn)
    chain32 = compute_component_children('c3', comp_conn)
    chain42 = compute_component_children('c4', comp_conn)
    chain52 = compute_component_children('c5', comp_conn)

    components_range2 = ['c1', 'c1', 'c2', 'c2', 'c4', 'c4', 'c4', 'c3', 'c5', 'c5', 'c6']
    component_nodes2 = compute_component_nodes(components_range2)
    component_father2 = compute_component_father(comp_conn2)
    prevnodes2 = compute_prevnode(components_range2, component_nodes2, component_father2)
