# Simulation scope

The current engineering tools provide bounded implementations with explicit inputs and checks. They do not make every AI-generated shape automatically suitable for simulation.

| Tool family | Current scope | Important exclusions |
| --- | --- | --- |
| Thermal | 3D steady conduction on supported meshed solids | Transient/radiation/coupled thermal-fluid analysis is not claimed |
| Mechanical | 3D small-displacement linear elasticity with supported boundary conditions | Contact, plasticity, fracture and nonlinear deformation are unavailable |
| Fluid | Creeping-flow Stokes in supported domains | General inertial, turbulent or compressible CFD is unavailable |
| Reference studies | Reduced 1D rectangular beam and fin examples | These do not solve arbitrary selected assemblies |
| Assembly motion | Bounded geometric joints and checks | General dynamics and contact simulation are unavailable |

Before a solve, identify the current model/revision, material constants with units, domain, loads, constraints and boundary selections. Inspect actual mesh quality. Report solver residuals, boundary assumptions, convergence evidence and unsupported conditions. Save results against their originating artifact; display stale results as stale after geometry changes.

AI-written explanations are not numerical evidence. Mesh convergence and agreement with an analytical benchmark support only the tested domain, not universal accuracy. Read the detailed [engineering contracts](../plugin/skills/intact-cad/references/priority23.md) for tool schemas and current limits.
