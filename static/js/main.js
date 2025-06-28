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

function fetchMoves(name, level, allowTM, moveContainerId) {
  const pokemon = allPokemonData[name];
  const legalMoves = new Set();
  const numericLevel = parseInt(level) || 1;

  // Add level-up moves if Pokémon's level is high enough
  if (pokemon.learnset && Array.isArray(pokemon.learnset.level_up)) {
    for (const move of pokemon.learnset.level_up) {
      if (level >= move.level) {
        legalMoves.add(move.name);
      }
    }
  }

  // Always add TM/HM moves if toggle is checked
  if (allowTM && pokemon.learnset) {
    if (Array.isArray(pokemon.learnset.tm)) {
      for (const move of pokemon.learnset.tm) {
        legalMoves.add(move);
      }
    }
    if (Array.isArray(pokemon.learnset.hm)) {
      for (const move of pokemon.learnset.hm) {
        legalMoves.add(move);
      }
    }
  }

  // Turn move names into full move data
  const fullMoves = Array.from(legalMoves)
    .map(moveName => allMovesData[moveName])
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));

  renderMoveOptions(moveContainerId, fullMoves);
}

function renderMoveDropdowns(role, moves) {
  for (let i = 1; i <= 4; i++) {
    const select = document.getElementById(`${role}-move-${i}`);
    if (!select) continue;

    // Preserve selected value if possible
    const previousValue = select.value;
    select.innerHTML = "";

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "-- Select Move --";
    select.appendChild(defaultOption);

    moves.forEach(move => {
      const option = document.createElement("option");
      option.value = move.name;
      option.textContent = move.name;
      option.title = `Type: ${move.type}\nPower: ${move.power}\nAccuracy: ${move.accuracy}\n${move.description}`;
      select.appendChild(option);
    });

    // Restore previously selected move if still available
    if (Array.from(select.options).some(opt => opt.value === previousValue)) {
      select.value = previousValue;
    }

    select.addEventListener("change", () => {
      updateDropdownExclusions(role);
    });
  }

  updateDropdownExclusions(role);
}

function updateDropdownExclusions(role) {
  const selected = new Set();

  for (let i = 1; i <= 4; i++) {
    const val = document.getElementById(`${role}-move-${i}`)?.value;
    if (val) selected.add(val);
  }

  for (let i = 1; i <= 4; i++) {
    const select = document.getElementById(`${role}-move-${i}`);
    if (!select) continue;

    const current = select.value;

    Array.from(select.options).forEach(option => {
      if (option.value && option.value !== current) {
        option.disabled = selected.has(option.value);
      } else {
        option.disabled = false;
      }
    });
  }
}

function updateDropdownOptions(dropdowns) {
  const selectedMoves = dropdowns.map(drop => drop.value).filter(Boolean);

  dropdowns.forEach(drop => {
    const currentValue = drop.value;
    Array.from(drop.options).forEach(option => {
      if (option.value === "") return;
      option.disabled = selectedMoves.includes(option.value) && option.value !== currentValue;
    });
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

function drawStatsChart(role, baseStats, level) {
  const statNames = ["HP", "Attack", "Defense", "Special Attack", "Special Defense", "Speed"];
  const calculatedStats = [
    calculateHP(baseStats.hp, level),
    calculateOtherStat(baseStats.attack, level),
    calculateOtherStat(baseStats.defense, level),
    calculateOtherStat(baseStats.special_attack, level),
    calculateOtherStat(baseStats.special_defense, level),
    calculateOtherStat(baseStats.speed, level),
  ];

  const ctxId = `${role}-stats`;
  const container = document.getElementById(ctxId);
  container.innerHTML = `<canvas id="${ctxId}-canvas"></canvas>`;
  const ctx = document.getElementById(`${ctxId}-canvas`);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: statNames,
      datasets: [{
        label: `${role} stats at level ${level}`,
        data: calculatedStats,
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 400
        }
      }
    }
  });
}

function calculateHP(base, level) {
  return Math.floor(((2 * base * level) / 100) + level + 10);
}

function calculateOtherStat(base, level) {
  return Math.floor(((2 * base * level) / 100) + 5);
}

function getLegalMoves(name, level, allowTM) {
  const pokemon = allPokemonData[name];
  const legalMoves = new Set();
  const numericLevel = parseInt(level) || 1;

  if (pokemon.learnset && Array.isArray(pokemon.learnset.level_up)) {
    for (const move of pokemon.learnset.level_up) {
      if (numericLevel >= move.level) {
        legalMoves.add(move.name);
      }
    }
  }

  if (allowTM && pokemon.learnset) {
    if (Array.isArray(pokemon.learnset.tm)) {
      pokemon.learnset.tm.forEach(move => legalMoves.add(move));
    }
    if (Array.isArray(pokemon.learnset.hm)) {
      pokemon.learnset.hm.forEach(move => legalMoves.add(move));
    }
  }

  return Array.from(legalMoves)
    .map(name => allMovesData[name])
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
}

async function updateMoves(role) {
    const name = document.getElementById(`${role}-name`).value;
    const level = parseInt(document.getElementById(`${role}-level`).value) || 1;
    const tm = document.getElementById(`${role}-tm-toggle`).checked;
    console.log(`Updating moves for ${name} at level ${level}, TM toggle = ${tm}`);
    const moves = getLegalMoves(name, level, tm);
    renderMoveDropdowns(role, moves);


    // Update image
    function normalizeName(name) {
      return name
        .toLowerCase()
        .replace("♀", "f")
        .replace("♂", "m")
        .replace(/[^a-z0-9]/g, "-") // replaces spaces, apostrophes, periods, etc.
        .replace(/-+/g, "-"); // collapses multiple hyphens
    }

    const imageElement = document.getElementById(`${role}-image`);
    if (imageElement) {
      imageElement.src = `static/images/${normalizeName(name)}.jpg`;
      imageElement.alt = name;
    }

    // Update stats
    const pokemon = allPokemonData[name];
    if (!pokemon || !pokemon.base_stats) {
      console.error(`Missing stats for Pokémon: ${name}`);
      return;
    }
    drawStatsChart(role, pokemon.base_stats, level)
}

document.getElementById("battle-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const getData = (role) => {
  const name = document.getElementById(`${role}-name`).value;
  const level = parseInt(document.getElementById(`${role}-level`).value);
  const pokemonInfo = allPokemonData[name];

  const selectedMoveNames = [];
  for (let i = 1; i <= 4; i++) {
    const val = document.getElementById(`${role}-move-${i}`)?.value;
    if (val) selectedMoveNames.push(val);
  }

  const fullMoves = selectedMoveNames.map(name => allMovesData[name]);

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
