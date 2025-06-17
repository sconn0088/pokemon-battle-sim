let allPokemonData = {};
let allMovesData = {};

Promise.all([
  fetch("/static/data/pokemon.json").then(res => res.json()),
  fetch("/static/data/moves.json").then(res => res.json())
]).then(([pokemonData, movesData]) => {
  allPokemonData = pokemonData;
  allMovesData = movesData;

  const names = Object.keys(allPokemonData);
  populateSelect("player-name", names);
  populateSelect("opponent-name", names);
  updateMoves("player");
  updateMoves("opponent");

  ["player", "opponent"].forEach(role => {
    document.getElementById(`${role}-name`).addEventListener("change", () => updateMoves(role));
    document.getElementById(`${role}-level`).addEventListener("input", () => updateMoves(role));
    document.getElementById(`${role}-tm-toggle`).addEventListener("change", () => updateMoves(role));
  });
});

async function fetchPokemonNames() {
    const res = await fetch("/api/pokemon");
    return await res.json();
}

async function fetchMoves(name, level, allowTM, moveContainerId) {
    const response = await fetch(`/api/moves?name=${name}&level=${level}&tm=${allowTM}`);
    const moves = await response.json();
    renderMoveOptions(moveContainerId, moves);
}

function renderMoveOptions(containerId, moves) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    const info = document.createElement("p");
    info.textContent = "Choose up to 4 moves:";
    container.appendChild(info);

    moves.forEach((move, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "move";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `${containerId}-move-${index}`;
    checkbox.name = `${containerId}-move`;
    checkbox.value = move.name;

    const label = document.createElement("label");
    label.htmlFor = checkbox.id;
    label.textContent = move.name;
    label.title = `Type: ${move.type}\nPower: ${move.power}\nAccuracy: ${move.accuracy}\nDescription: ${move.description}`;

    checkbox.addEventListener("change", () => {
        const checkedCount = container.querySelectorAll("input[type=checkbox]:checked").length;
        const allCheckboxes = container.querySelectorAll("input[type=checkbox]");
        allCheckboxes.forEach(cb => {
        if (!cb.checked) cb.disabled = checkedCount >= 4;
        });
    });

    wrapper.appendChild(checkbox);
    wrapper.appendChild(label);
    container.appendChild(wrapper);
    });
}

function populateSelect(selectId, names) {
    const select = document.getElementById(selectId);
    select.innerHTML = "";
    names.forEach(name => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    select.appendChild(option);
    });
}

async function updateMoves(role) {
    const name = document.getElementById(`${role}-name`).value;
    const level = document.getElementById(`${role}-level`).value;
    const tm = document.getElementById(`${role}-tm-toggle`).checked;
    await fetchMoves(name, level, tm, `${role}-move-options`);
}

document.getElementById("battle-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const getData = (role) => {
    const name = document.getElementById(`${role}-name`).value;
    const level = parseInt(document.getElementById(`${role}-level`).value);
    const selectedMoveNames = Array.from(document.querySelectorAll(`#${role}-move-options input:checked`)).map(cb => cb.value);
    const fullMoves = selectedMoveNames.map(moveName => allMovesData[moveName]);

    const pokemonInfo = allPokemonData[name];

    return {
      name,
      level,
      types: pokemonInfo.types,
      base_stats: pokemonInfo.base_stats,
      moves: fullMoves
    };
  };

  const player = getData("player");
  const opponent = getData("opponent");

  if (player.moves.length === 0 || player.moves.length > 4 ||
      opponent.moves.length === 0 || opponent.moves.length > 4) {
    alert("Please select between 1 and 4 moves for both Pokémon.");
    return;
  }

  document.getElementById("result").innerHTML = "<p>Simulating battle...</p>";

  try {
    const res = await fetch("/api/battle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player, opponent })
    });

    const data = await res.json();

    if (data.result) {
      document.getElementById("result").innerHTML = `<p>${data.result}</p>`;
    } else {
      document.getElementById("result").innerHTML = `<p>Error: ${data.error}</p>`;
    }

    if (data.battle_log) {
      const blob = new Blob([data.battle_log], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);

      const button = document.getElementById("download-log");
      button.href = url;
      button.download = "battle_log.txt";
      button.style.display = "inline-block";
    }
  } catch (err) {
    document.getElementById("result").innerHTML = `<p>Error: ${err.message}</p>`;
  }
});
