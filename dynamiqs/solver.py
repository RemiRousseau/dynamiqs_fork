from __future__ import annotations

from typing import ClassVar

import equinox as eqx

from .gradient import Autograd, CheckpointAutograd, Gradient

__all__ = ['Propagator', 'Euler', 'Rouchon1', 'Rouchon2', 'Dopri5', 'Dopri8', 'Tsit5']


# === generic solvers options
class Solver(eqx.Module):
    SUPPORTED_GRADIENT: ClassVar[tuple[type[Gradient], ...]] = ()

    @classmethod
    def supports_gradient(cls, gradient: Gradient | None) -> bool:  # noqa: ANN102
        return isinstance(gradient, cls.SUPPORTED_GRADIENT)

    @classmethod
    def assert_supports_gradient(cls, gradient: Gradient | None) -> None:  # noqa: ANN102
        if gradient is not None and not cls.supports_gradient(gradient):
            support_str = ', '.join(f'`{x.__name__}`' for x in cls.SUPPORTED_GRADIENT)
            raise ValueError(
                f'Solver `{cls.__name__}` does not support gradient'
                f' `{type(gradient).__name__}` (supported gradient types:'
                f' {support_str}).'
            )


# === propagator solvers options
class Propagator(Solver):
    SUPPORTED_GRADIENT = (Autograd,)

    def __init__(self):
        r"""Quantum propagator method.

        Explicitly compute the propagator to evolve the state between each time in
        `tsave`.

        For the Schrödinger equation with constant Hamiltonian $H$, the propagator to
        evolve the state from time $t_0$ to time $t_1$ is an $n\times n$ matrix given by
        $$
            U(t_0, t_1) = \exp(-i (t_1 - t_0) H).
        $$

        For the Lindblad master equation with constant Liouvillian $\mathcal{L}$, the
        problem is vectorized and the propagator to evolve the state from time $t_0$ to
        time $t_1$ is an $n^2\times n^2$ matrix given by
        $$
            \mathcal{U}(t_0, t_1) = \exp((t_1 - t_0)\mathcal{L}).
        $$

        Warning:
            This solver is not recommended for open systems of large dimension, due to
            the $\mathcal{O}(n^6)$ scaling of computing the Liouvillian exponential.

        Warning: Constant Hamiltonian and jump operators only
            The propagator method only supports constant Hamiltonian and jump
            operators. Piecewise-constant problems will also be supported in the future.
        """


# === generic ODE solvers options
class _ODESolver(Solver):
    pass


class _ODEFixedStep(_ODESolver):
    dt: float


class _ODEAdaptiveStep(_ODESolver):
    rtol: float = 1e-6
    atol: float = 1e-6
    safety_factor: float = 0.9
    min_factor: float = 0.2
    max_factor: float = 5.0
    max_steps: int = 100_000


# === diffrax-based solvers options
class _DiffraxSolver(Solver):
    SUPPORTED_GRADIENT = (Autograd, CheckpointAutograd)


# === public solvers options
class Euler(_DiffraxSolver, _ODEFixedStep):
    def __init__(self, dt: float):
        """Euler method (fixed step size ODE solver).

        This solver is implemented by the amazing [Diffrax](https://docs.kidger.site/diffrax/) library, see
        [`diffrax.Euler`](https://docs.kidger.site/diffrax/api/solvers/ode_solvers/#diffrax.Euler).

        Warning:
            This solver is not recommended for general use.

        Args:
            dt _(float)_: Fixed time step.
        """  # noqa: E501
        _ODEFixedStep.__init__(self, dt)


class Rouchon1(_DiffraxSolver, _ODEFixedStep):
    def __init__(self, dt: float):
        """First-order Rouchon method (fixed step size ODE solver).

        Warning:
            This solver has not been ported to JAX yet.
        """
        _ODEFixedStep.__init__(self, dt)

    # normalize: The default scheme is trace-preserving at first order only. This
    # parameter sets the normalisation behaviour:
    # - `None`: The scheme is not normalized.
    # - `'sqrt'`: The Kraus map is renormalized with a matrix square root. Ideal
    #   for stiff problems, recommended for time-independent problems.
    # - `cholesky`: The Kraus map is renormalized at each time step using a Cholesky
    #   decomposition. Ideal for stiff problems, recommended for time-dependent
    #   problems.

    # TODO: fix, strings are not valid JAX types
    # normalize: Literal['sqrt', 'cholesky'] | None = None


class Rouchon2(_DiffraxSolver, _ODEFixedStep):
    def __init__(self, dt: float):
        """Second-order Rouchon method (fixed step size ODE solver).

        Warning:
            This solver has not been ported to JAX yet.
        """
        _ODEFixedStep.__init__(self, dt)


class Dopri5(_DiffraxSolver, _ODEAdaptiveStep):
    def __init__(
        self,
        rtol: float = 1e-6,
        atol: float = 1e-6,
        safety_factor: float = 0.9,
        min_factor: float = 0.2,
        max_factor: float = 5.0,
        max_steps: int = 100_000,
    ):
        """Dormand-Prince method of order 5 (adaptive step size ODE solver).

        This solver is implemented by the amazing [Diffrax](https://docs.kidger.site/diffrax/) library, see
        [`diffrax.Dopri5`](https://docs.kidger.site/diffrax/api/solvers/ode_solvers/#diffrax.Dopri5).

        Args:
            rtol: Relative tolerance.
            atol: Absolute tolerance.
            safety_factor: Safety factor for adaptive step sizing.
            min_factor: Minimum factor for adaptive step sizing.
            max_factor: Maximum factor for adaptive step sizing.
            max_steps: Maximum number of steps.
        """  # noqa: E501
        _ODEAdaptiveStep.__init__(
            self, rtol, atol, safety_factor, min_factor, max_factor, max_steps
        )


class Dopri8(_DiffraxSolver, _ODEAdaptiveStep):
    def __init__(
        self,
        rtol: float = 1e-6,
        atol: float = 1e-6,
        safety_factor: float = 0.9,
        min_factor: float = 0.2,
        max_factor: float = 5.0,
        max_steps: int = 100_000,
    ):
        """Dormand-Prince method of order 8 (adaptive step size ODE solver).

        This solver is implemented by the amazing [Diffrax](https://docs.kidger.site/diffrax/) library, see
        [`diffrax.Dopri8`](https://docs.kidger.site/diffrax/api/solvers/ode_solvers/#diffrax.Dopri8).

        Args:
            rtol: Relative tolerance.
            atol: Absolute tolerance.
            safety_factor: Safety factor for adaptive step sizing.
            min_factor: Minimum factor for adaptive step sizing.
            max_factor: Maximum factor for adaptive step sizing.
            max_steps: Maximum number of steps.
        """  # noqa: E501
        _ODEAdaptiveStep.__init__(
            self, rtol, atol, safety_factor, min_factor, max_factor, max_steps
        )


class Tsit5(_DiffraxSolver, _ODEAdaptiveStep):
    def __init__(
        self,
        rtol: float = 1e-6,
        atol: float = 1e-6,
        safety_factor: float = 0.9,
        min_factor: float = 0.2,
        max_factor: float = 5.0,
        max_steps: int = 100_000,
    ):
        """Tsitouras method of order 5 (adaptive step size ODE solver).

        This solver is implemented by the amazing [Diffrax](https://docs.kidger.site/diffrax/) library, see
        [`diffrax.Tsit5`](https://docs.kidger.site/diffrax/api/solvers/ode_solvers/#diffrax.Tsit5).

        Args:
            rtol: Relative tolerance.
            atol: Absolute tolerance.
            safety_factor: Safety factor for adaptive step sizing.
            min_factor: Minimum factor for adaptive step sizing.
            max_factor: Maximum factor for adaptive step sizing.
            max_steps: Maximum number of steps.
        """  # noqa: E501
        _ODEAdaptiveStep.__init__(
            self, rtol, atol, safety_factor, min_factor, max_factor, max_steps
        )
