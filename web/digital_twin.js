const THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js";

function colorForRisk(level) {
  return {
    critical: 0xef4444,
    high: 0xf97316,
    medium: 0xeab308,
    low: 0x22c55e,
  }[String(level || "low").toLowerCase()] || 0x22c55e;
}

function colorForHealth(score) {
  const health = Number(score || 0);
  if (health >= 90) return 0x00e676;
  if (health >= 70) return 0xffb300;
  return 0xff5252;
}

function makeLabel(THREE, text) {
  const canvas = document.createElement("canvas");
  canvas.width = 320;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  context.fillStyle = "rgba(7, 16, 18, 0.82)";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = "rgba(20, 184, 166, 0.55)";
  context.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
  context.fillStyle = "#edf5f4";
  context.font = "700 24px Segoe UI, Arial";
  const lines = String(text).split("\n").slice(0, 3);
  lines.forEach((line, index) => context.fillText(line.slice(0, 28), 18, 30 + index * 27));
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(4.8, 1.4, 1);
  return sprite;
}

function clearPrevious(container) {
  if (container.__twinCleanup) {
    container.__twinCleanup();
    container.__twinCleanup = null;
  }
  container.innerHTML = "";
}

async function setup() {
  try {
    const THREE = await import(THREE_URL);
    window.MaintenanceDigitalTwin = {
      render(container, data, onSelect) {
        if (!container || !data) return false;
        clearPrevious(container);
        const width = Math.max(640, container.clientWidth || 900);
        const height = Math.max(460, container.clientHeight || 520);
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x07111d);
        const camera = new THREE.PerspectiveCamera(48, width / height, 0.1, 1000);
        camera.position.set(0, 42, 46);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setSize(width, height);
        container.appendChild(renderer.domElement);

        scene.add(new THREE.HemisphereLight(0xb7fff6, 0x101010, 1.4));
        const key = new THREE.DirectionalLight(0xffffff, 1.3);
        key.position.set(20, 34, 20);
        scene.add(key);

        const floor = new THREE.Mesh(
          new THREE.BoxGeometry(64, 0.4, 38),
          new THREE.MeshStandardMaterial({ color: 0x0d1b2a, metalness: 0.32, roughness: 0.58 })
        );
        floor.position.y = -0.25;
        scene.add(floor);

        const grid = new THREE.GridHelper(64, 24, 0x00d4ff, 0x12263a);
        grid.position.y = 0.02;
        scene.add(grid);

        const interactives = [];
        const zones = data.zones || [];
        const zoneMap = {
          "Blast Furnace": [-22, 0, -8, 7, 13, 8],
          "Steel Melting Shop": [-4, 0, -10, 14, 6, 10],
          "Rolling Mill": [20, 0, -6, 22, 4, 7],
          "Coke Oven": [-24, 0, 12, 16, 4, 8],
          "Sinter Plant": [-3, 0, 13, 15, 4, 8],
          Utilities: [22, 0, 13, 16, 5, 8],
        };

        zones.forEach((zone) => {
          const [x, y, z, sx, sy, sz] = zoneMap[zone.name] || [0, 0, 0, 8, 4, 8];
          const zoneMesh = new THREE.Mesh(
            new THREE.BoxGeometry(sx, sy, sz),
            new THREE.MeshStandardMaterial({
              color: colorForHealth(zone.health_score),
              emissive: colorForRisk(zone.risk_level),
              emissiveIntensity: 0.08,
              transparent: true,
              opacity: 0.18,
              metalness: 0.15,
              roughness: 0.55,
            })
          );
          zoneMesh.position.set(x, y + sy / 2, z);
          scene.add(zoneMesh);
          const label = makeLabel(THREE, `${zone.name}\n${zone.health_score}% health`);
          label.position.set(x, sy + 2.6, z);
          scene.add(label);

          (zone.assets || []).forEach((asset, index) => {
            const localX = x - sx / 2 + 2.2 + (index % 3) * Math.max(3, sx / 3);
            const localZ = z - sz / 2 + 2.1 + Math.floor(index / 3) * 3.2;
            const height = 1.3 + Number(asset.health_score || 50) / 45;
            const node = new THREE.Mesh(
              new THREE.CylinderGeometry(0.72, 0.9, height, 18),
              new THREE.MeshStandardMaterial({
                color: colorForHealth(asset.health_score),
                emissive: colorForRisk(asset.risk_level),
                emissiveIntensity: asset.risk_level === "critical" ? 0.42 : 0.18,
                metalness: 0.38,
                roughness: 0.34,
              })
            );
            node.position.set(localX, height / 2 + 0.1, localZ);
            node.userData.baseScale = 1;
            node.userData.asset = asset;
            scene.add(node);
            interactives.push(node);

            const ring = new THREE.Mesh(
              new THREE.TorusGeometry(1.25, 0.035, 10, 42),
              new THREE.MeshBasicMaterial({
                color: colorForRisk(asset.risk_level),
                transparent: true,
                opacity: asset.risk_level === "critical" ? 0.82 : 0.42,
              })
            );
            ring.rotation.x = Math.PI / 2;
            ring.position.set(localX, 0.08, localZ);
            ring.userData.followAsset = node;
            ring.userData.critical = asset.risk_level === "critical";
            scene.add(ring);

            const assetLabel = makeLabel(THREE, `${asset.name}\n${asset.health_score}% / ${asset.risk_level}\nRUL ${asset.rul_hours} h`);
            assetLabel.position.set(localX, height + 2.2, localZ);
            assetLabel.scale.set(3.2, 0.95, 1);
            scene.add(assetLabel);
          });
        });

        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();
        function handleClick(event) {
          const rect = renderer.domElement.getBoundingClientRect();
          pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
          raycaster.setFromCamera(pointer, camera);
          const hit = raycaster.intersectObjects(interactives, false)[0];
          if (hit?.object?.userData?.asset && typeof onSelect === "function") {
            onSelect(hit.object.userData.asset.id);
          }
        }
        renderer.domElement.addEventListener("click", handleClick);

        let frame = 0;
        let active = true;
        function animate() {
          if (!active) return;
          frame += 0.01;
          scene.rotation.y = Math.sin(frame) * 0.025;
          scene.traverse((object) => {
            if (object.userData?.asset) {
              const critical = object.userData.asset.risk_level === "critical";
              const pulse = critical ? 1 + Math.sin(frame * 4) * 0.055 : 1 + Math.sin(frame * 2) * 0.015;
              object.scale.set(pulse, pulse, pulse);
            }
            if (object.userData?.followAsset) {
              const critical = object.userData.critical;
              const pulse = critical ? 1 + Math.sin(frame * 4) * 0.1 : 1 + Math.sin(frame * 2) * 0.025;
              object.scale.set(pulse, pulse, pulse);
              object.material.opacity = critical ? 0.62 + Math.sin(frame * 4) * 0.18 : 0.32;
            }
          });
          renderer.render(scene, camera);
          requestAnimationFrame(animate);
        }
        animate();

        container.__twinCleanup = () => {
          active = false;
          renderer.domElement.removeEventListener("click", handleClick);
          renderer.dispose();
          scene.traverse((object) => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
              if (object.material.map) object.material.map.dispose();
              object.material.dispose();
            }
          });
        };
        return true;
      },
    };
  } catch (error) {
    window.MaintenanceDigitalTwin = null;
  } finally {
    window.dispatchEvent(new CustomEvent("maintenance-digital-twin-ready"));
  }
}

setup();
