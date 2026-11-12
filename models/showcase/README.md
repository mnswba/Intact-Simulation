# Original Intact showcase models

Twenty inspectable CAD concepts used in the [Finished Work gallery](https://www.intactsimulation.com/finished-work/). These are original showcase studies, not manufactured or performance-certified products. Native solids support STEP; sampled TPMS meshes support GLB/STL/3MF without smooth analytic STEP.

| Model | Category | Parts | Source |
|---|---|---:|---|
| [Cairn Six-Wheel Rover](https://www.intactsimulation.com/demo/?model=cairn-six-wheel-rover) | Robotics | 42 | [Python](robotics/cairn-six-wheel-rover.py) |
| [Ember Six-Axis Arm](https://www.intactsimulation.com/demo/?model=ember-six-axis-arm) | Robotics | 30 | [Python](robotics/ember-six-axis-arm.py) |
| [Finch Adaptive Gripper](https://www.intactsimulation.com/demo/?model=finch-adaptive-gripper) | Robotics | 30 | [Python](robotics/finch-adaptive-gripper.py) |
| [Kelp Quadruped Inspector](https://www.intactsimulation.com/demo/?model=kelp-quadruped-inspector) | Robotics | 39 | [Python](robotics/kelp-quadruped-inspector.py) |
| [Lumen Humanoid Service Robot](https://www.intactsimulation.com/demo/?model=lumen-humanoid-service-robot) | Robotics | 43 | [Python](robotics/lumen-humanoid-service-robot.py) |
| [Grooved piston & split connecting rod](https://www.intactsimulation.com/demo/?model=piston_rod) | Engine & powertrain | 9 | [Python](powertrain/piston_rod.py) |
| [Inline-four crankshaft](https://www.intactsimulation.com/demo/?model=inline_four_crankshaft) | Engine & powertrain | 19 | [Python](powertrain/inline_four_crankshaft.py) |
| [Sectioned turbocharger concept](https://www.intactsimulation.com/demo/?model=sectioned_turbocharger) | Engine & powertrain | 20 | [Python](powertrain/sectioned_turbocharger.py) |
| [Open DOHC cylinder head](https://www.intactsimulation.com/demo/?model=dohc_cylinder_head) | Engine & powertrain | 27 | [Python](powertrain/dohc_cylinder_head.py) |
| [Planetary reduction gearbox](https://www.intactsimulation.com/demo/?model=planetary_reduction_gearbox) | Engine & powertrain | 14 | [Python](powertrain/planetary_reduction_gearbox.py) |
| [Battery thermal-management concept](https://www.intactsimulation.com/demo/?model=battery_thermal_concept) | Product concepts | 36 | [Python](products/battery_thermal_concept.py) |
| [Inspection quadrotor concept](https://www.intactsimulation.com/demo/?model=inspection_quadrotor) | Product concepts | 32 | [Python](products/inspection_quadrotor.py) |
| [Desktop air-quality monitor concept](https://www.intactsimulation.com/demo/?model=desktop_air_monitor) | Product concepts | 18 | [Python](products/desktop_air_monitor.py) |
| [Helical vertical-axis turbine concept](https://www.intactsimulation.com/demo/?model=helical_vertical_turbine) | Product concepts | 21 | [Python](products/helical_vertical_turbine.py) |
| [Liquid-cooled compute module concept](https://www.intactsimulation.com/demo/?model=liquid_cooled_compute) | Product concepts | 34 | [Python](products/liquid_cooled_compute.py) |
| [Gradient gyroid core](https://www.intactsimulation.com/demo/?model=gradient-gyroid-core) | TPMS | 1 | [Python](tpms/gradient-gyroid-core.py) |
| [Schwarz P flow column](https://www.intactsimulation.com/demo/?model=schwarz-flow-column) | TPMS | 1 | [Python](tpms/schwarz-flow-column.py) |
| [Diamond exchanger core](https://www.intactsimulation.com/demo/?model=diamond-exchanger-core) | TPMS | 1 | [Python](tpms/diamond-exchanger-core.py) |
| [Neovius porous sphere](https://www.intactsimulation.com/demo/?model=neovius-porous-sphere) | TPMS | 1 | [Python](tpms/neovius-porous-sphere.py) |
| [Lidinoid lattice panel](https://www.intactsimulation.com/demo/?model=lidinoid-lattice-panel) | TPMS | 1 | [Python](tpms/lidinoid-lattice-panel.py) |

Read the chosen Python source and pass it to Intact `build_model` with the parameters in [`website/content/showcase.json`](../../website/content/showcase.json). Generated source must execute through the Linux CAD sandbox. Rebuild ZIPs with the installed runtime Python:

```sh
python website/build-showcase.py --state-dir /tmp/intact-showcase-rebuild
```

Use a disposable state directory. The script refuses the default personal CAD directory. Geometry outputs are ignored by Git; public download links and sources are tracked. The browser demo loads actual GLBs and uses original named parts for selection, display colors and explosion. No model training is performed by adding examples.
