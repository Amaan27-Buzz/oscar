// One physical object survives navigation, input changes and interrupted transitions.
export function createPresence(element, reduced) {
  const puck = element.querySelector('.puck');
  let x = 0, y = 2, vx = 0, vy = 0, tx = 0, ty = 2, frame = 0, previous = 0;
  const positions = { Ready: [0, 2], Listening: [0, -10], Speaking: [7, -4], Working: [-8, 4], Verifying: [-3, -4], Waiting: [5, 8], Blocked: [0, 11], Alert: [0, -6] };
  function draw() { puck.style.transform = `translate(${x * 1.6}px, ${y * 1.6}px)`; }
  function tick(time) {
    const dt = Math.min((time - previous) / 1000 || 1 / 60, 0.032); previous = time;
    vx += ((tx - x) * 210 - vx * 24) * dt;
    vy += ((ty - y) * 210 - vy * 24) * dt;
    x += vx * dt; y += vy * dt; draw();
    if (Math.abs(tx - x) + Math.abs(ty - y) + Math.abs(vx) + Math.abs(vy) > 0.06) frame = requestAnimationFrame(tick);
    else { frame = 0; x = tx; y = ty; draw(); }
  }
  return (state, quiet = false) => {
    [tx, ty] = quiet ? [0, 2] : positions[state];
    element.dataset.state = state;
    if (reduced()) { cancelAnimationFrame(frame); frame = 0; x = tx; y = ty; vx = vy = 0; draw(); }
    else if (!frame) { previous = 0; frame = requestAnimationFrame(tick); }
  };
}
