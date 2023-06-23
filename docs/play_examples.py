import jax.numpy as jnp
from jax import jit
import jax
from functools import partial

@jit
def reshape_arrays(x: jnp.ndarray):

    x2 = jnp.reshape(x, (int(x.shape[0] / 6), 6))
    return x2

@jit
def insert_arrays(x: jnp.ndarray, n):

    x2 = jnp.reshape(x, (int(x.shape[0] / 6), 6))
    x3 = jnp.insert(x2, n, jnp.zeros(6), axis=0)
    return x3

@partial(jit, static_argnames=['n'])
#@jit
def return_arrays(x: jnp.ndarray, n):

    x2 = x[:, :n]
    x3 = jnp.reshape(x2, (int(x2.shape[0] / 6), 6, n))

    return x3


a = jnp.array([i for i in range(6*3)])
x = reshape_arrays(a)
x2= insert_arrays(a,2)
#x3= return_arrays(jnp.array([i for i in range(6*4)]).reshape(), 3)


#f = jax.vmap(lambda u, v: jnp.matmul(u, v.T).T, in_axes=(0,1), out_axes=1)
f = jax.vmap(lambda u, v: jnp.matmul(v, u.T), in_axes=(0,1), out_axes=1)
u = jnp.array([jnp.eye(6) for i in range(3)])
v = jnp.arange(4*6*3).reshape((4, 3, 6))
fuv = f(u, v)

