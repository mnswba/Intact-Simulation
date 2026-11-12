// User-provided scout-driving-source controller. Adaptation: allow 1–16 assemblies; original eight-second trajectory retained.
/**
 * Integration adapter prepared for the Intact viewer.
 * The exact original preview runtime is animation.js; this module extracts its
 * driving logic for an existing THREE scene. It performs kinematic preview only.
 *
 * Contract: root's LOCAL frame uses metres, CAD +X forward, +Y left, +Z up.
 * Wrap this root with the viewer's display-normalization/Y-up transform.
 * Never save these temporary transforms to the native CAD specification.
 */
export function createVehicleDriveController({
  THREE, root, wheelAssemblies, radius = 0.165, speed = 0.30,
  onChange = () => {},
}) {
  if (!THREE || !root) throw new Error('THREE and the CAD-space root are required.');
  if (!(radius > 0) || !(speed >= 0)) throw new Error('Invalid wheel radius or speed.');
  if (!Array.isArray(wheelAssemblies) || wheelAssemblies.length < 1 || wheelAssemblies.length > 16)
    throw new Error('Provide 1–16 bound wheel assemblies.');
  if (Math.max(root.scale.x, root.scale.y, root.scale.z) - Math.min(root.scale.x, root.scale.y, root.scale.z) > 1e-8)
    throw new Error('Use a uniformly scaled CAD-space root.');

  const rest = {
    position: root.position.clone(), quaternion: root.quaternion.clone(),
    scale: root.scale.clone(), matrix: root.matrix.clone(),
    matrixAutoUpdate: root.matrixAutoUpdate,
  };
  if (!root.matrixAutoUpdate) root.matrix.decompose(root.position, root.quaternion, root.scale);
  root.matrixAutoUpdate = true;
  const startPosition = root.position.clone();
  const driveDirection = new THREE.Vector3(1, 0, 0)
    .applyQuaternion(root.quaternion).multiplyScalar(root.scale.x);
  root.updateMatrixWorld(true);

  const originals = [], groups = [], seen = new Set();
  // Validate before changing the scene graph.
  for (const wheel of wheelAssemblies) {
    if (!Array.isArray(wheel.pivot) || wheel.pivot.length !== 3 || !wheel.parts?.length)
      throw new Error('Each wheel needs a pivot and rotating parts.');
    for (const part of wheel.parts) {
      if (!part?.parent || seen.has(part)) throw new Error('Missing or duplicate rotating part.');
      seen.add(part);
    }
  }
  for (const wheel of wheelAssemblies) {
    const group = new THREE.Group();
    group.name = '__drive_preview_' + wheel.id;
    group.userData.previewOnly = true;
    group.position.fromArray(wheel.pivot);
    root.add(group);
    group.updateMatrixWorld(true);
    for (const part of wheel.parts) {
      if (part.matrixAutoUpdate) part.updateMatrix();
      originals.push({part, parent: part.parent, matrix: part.matrix.clone(),
        matrixAutoUpdate: part.matrixAutoUpdate});
      group.attach(part); // Keep the assembled world pose while changing parent.
    }
    groups.push(group);
  }

  let time = 0, playing = false, disposed = false;
  const duration = 8, axle = new THREE.Vector3(0, 1, 0);
  function trajectory(t) {
    // 1 s acceleration, 5 s cruise, 1 s braking, 1 s stopped.
    if (t <= 1) return {distance: .5 * speed * t * t, velocity: speed * t};
    if (t <= 6) return {distance: .5 * speed + speed * (t - 1), velocity: speed};
    if (t <= 7) {
      const u = t - 6;
      return {distance: 5.5 * speed + speed * u - .5 * speed * u * u,
        velocity: speed * (1 - u)};
    }
    return {distance: 6 * speed, velocity: 0};
  }
  function getState() {
    const pose = trajectory(time);
    return {time, duration, playing, distance: pose.distance, speed: pose.velocity,
      wheelAngle: pose.distance / radius, mode: 'kinematic-preview'};
  }
  function ensureActive() { if (disposed) throw new Error('Controller has been disposed.'); }
  function setTime(value) {
    ensureActive();
    if (!Number.isFinite(value)) throw new Error('Time must be finite seconds.');
    time = Math.max(0, Math.min(duration, value));
    const state = getState();
    root.position.copy(startPosition).addScaledVector(driveDirection, state.distance);
    for (const group of groups) group.quaternion.setFromAxisAngle(axle, state.wheelAngle);
    root.updateMatrixWorld(true);
    onChange(state);
    return state;
  }
  function play() { ensureActive(); if (time >= duration) setTime(0); playing = true; return getState(); }
  function pause() { ensureActive(); playing = false; return getState(); }
  function update(deltaSeconds) {
    ensureActive();
    if (!Number.isFinite(deltaSeconds) || deltaSeconds < 0) throw new Error('Invalid frame delta.');
    if (playing) { setTime(time + deltaSeconds); if (time >= duration) playing = false; }
    return getState();
  }
  function dispose() {
    if (disposed) return;
    playing = false;
    setTime(0);
    for (const saved of originals) {
      saved.parent.attach(saved.part);
      saved.part.matrix.copy(saved.matrix);
      saved.part.matrix.decompose(saved.part.position, saved.part.quaternion, saved.part.scale);
      saved.part.matrixAutoUpdate = saved.matrixAutoUpdate;
    }
    for (const group of groups) root.remove(group);
    root.position.copy(rest.position); root.quaternion.copy(rest.quaternion); root.scale.copy(rest.scale);
    root.matrix.copy(rest.matrix); root.matrixAutoUpdate = rest.matrixAutoUpdate;
    root.updateMatrixWorld(true);
    disposed = true;
  }
  setTime(0);
  return {duration, play, pause, setTime, update, getState, dispose};
}

/** Resolve the stable part IDs used by this SCOUT model. */
export function scoutWheelAssemblies(root) {
  return ['front_left', 'front_right', 'rear_left', 'rear_right'].map(id => {
    const front = id.startsWith('front'), left = id.endsWith('left');
    const parts = ['tire_', 'rim_', 'hubcap_'].map(prefix => root.getObjectByName(prefix + id));
    if (parts.some(part => !part)) throw new Error('Missing wheel part for ' + id);
    return {id, pivot: [front ? .249 : -.249, left ? .2915 : -.2915, .165], parts};
  });
}
