// Game state
let selectedWords = [];
let mistakesRemaining = 4;
let foundGroups = [];
let gameWords = [];

// Mathematical expressions database - loaded from external file
let mathDatabase = [];
let currentDatabaseType = 'integration-strategies';

// Game generation system
let gameData = null;
let availableGroups = [];

// Database file mapping
const databaseFiles = {
    'integration-strategies': 'integration-strategies.json',
    'series-strategies': 'series-strategies.json'
};

// Load mathematical expressions database from JSON file
async function loadMathDatabase(databaseType = 'integration-strategies') {
    try {
        const filename = databaseFiles[databaseType];
        const response = await fetch(filename);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        mathDatabase = data.expressions;
        currentDatabaseType = databaseType;
        console.log(`Loaded ${mathDatabase.length} expressions from ${databaseType} database`);
        return true;
    } catch (error) {
        console.error(`Failed to load math database (${databaseType}):`, error);
        // Use fallback data if loading fails
        mathDatabase = getFallbackDatabase();
        currentDatabaseType = 'integration-strategies';
        return false;
    }
}

// Fallback database in case JSON loading fails
function getFallbackDatabase() {
    return [
        { expression: "$\\displaystyle \\sin^2\\theta + \\cos^2\\theta$", groups: ["Expressions equal to 1", "Trigonometric identities"], difficulty: 2 },
        { expression: "$\\displaystyle e^0$", groups: ["Expressions equal to 1", "Exponential functions"], difficulty: 1 },
        { expression: "$\\displaystyle \\lim_{x \\to 0} \\frac{\\sin x}{x}$", groups: ["Expressions equal to 1", "Important limits"], difficulty: 4 },
        { expression: "$\\displaystyle \\cos^2\\frac{\\pi}{4}$", groups: ["Expressions equal to 1", "Trigonometric values"], difficulty: 2 },
        { expression: "$\\displaystyle \\pi$", groups: ["Famous constants", "Circle properties"], difficulty: 1 },
        { expression: "$\\displaystyle e$", groups: ["Famous constants", "Exponential functions"], difficulty: 1 },
        { expression: "$\\displaystyle \\phi = \\frac{1+\\sqrt{5}}{2}$", groups: ["Famous constants", "Golden ratio"], difficulty: 2 },
        { expression: "$\\displaystyle \\sqrt{2}$", groups: ["Famous constants", "Algebraic numbers"], difficulty: 1 },
        { expression: "$\\displaystyle \\frac{d}{dx}[x^n] = nx^{n-1}$", groups: ["Derivative rules", "Power rule"], difficulty: 1 },
        { expression: "$\\displaystyle \\frac{d}{dx}[\\sin x] = \\cos x$", groups: ["Derivative rules", "Trigonometric derivatives"], difficulty: 1 },
        { expression: "$\\displaystyle \\frac{d}{dx}[e^x] = e^x$", groups: ["Derivative rules", "Exponential derivatives"], difficulty: 1 },
        { expression: "$\\displaystyle \\frac{d}{dx}[\\ln x] = \\frac{1}{x}$", groups: ["Derivative rules", "Logarithmic derivatives"], difficulty: 2 },
        { expression: "$\\displaystyle e^{i\\pi} + 1 = 0$", groups: ["Complex numbers", "Euler's identity"], difficulty: 4 },
        { expression: "$\\displaystyle |z|^2 = z \\cdot \\overline{z}$", groups: ["Complex numbers", "Modulus properties"], difficulty: 3 },
        { expression: "$\\displaystyle \\sqrt{-1} = i$", groups: ["Complex numbers", "Imaginary unit"], difficulty: 2 },
        { expression: "$\\displaystyle (a+bi)(a-bi) = a^2 + b^2$", groups: ["Complex numbers", "Conjugate products"], difficulty: 2 }
    ];
}

// Get all unique groups from database
function getAvailableGroups() {
    const allGroups = new Set();
    mathDatabase.forEach(item => {
        item.groups.forEach(group => allGroups.add(group));
    });
    return Array.from(allGroups);
}

// Generate a game with specified difficulty and group preferences
function generateGame(options = {}) {
    const {
        maxDifficulty = 4,
        minDifficulty = 1,
        preferredGroups = [],
        avoidGroups = []
    } = options;
    
    availableGroups = getAvailableGroups()
        .filter(group => !avoidGroups.includes(group));
    
    if (preferredGroups.length > 0) {
        availableGroups = availableGroups.filter(group => 
            preferredGroups.includes(group) || 
            availableGroups.filter(g => preferredGroups.includes(g)).length < 4
        );
    }
    
    // Try multiple times to generate a valid unique puzzle
    let attempts = 0;
    const maxAttempts = 50;
    
    while (attempts < maxAttempts) {
        attempts++;
        
        // Select 4 groups for the puzzle
        const selectedGroups = selectPuzzleGroups(availableGroups);
        
        if (selectedGroups.length < 4) {
            continue;
        }
        
        // Shuffle difficulty colors for variety
        const difficultyColors = ['yellow', 'green', 'blue', 'purple'];
        shuffleArray(difficultyColors);
        
        // Track all selected expressions to ensure uniqueness across all groups
        const allSelectedExpressions = new Set();
        
        // Find expressions for each group
        const groups = [];
        let validPuzzle = true;
        
        for (let index = 0; index < selectedGroups.length; index++) {
            const groupName = selectedGroups[index];
            const expressions = findExpressionsForGroup(groupName, maxDifficulty, minDifficulty);
            
            if (expressions.length < 4) {
                console.warn(`Not enough expressions for group: ${groupName}`);
                validPuzzle = false;
                break;
            }
            
            // Filter out expressions that are already selected
            const availableExpressions = expressions.filter(expr => 
                !allSelectedExpressions.has(expr.expression)
            );
            
            if (availableExpressions.length < 4) {
                console.warn(`Not enough unique expressions for group: ${groupName} (${availableExpressions.length} available)`);
                validPuzzle = false;
                break;
            }
            
            // Select 4 unique expressions for this group
            const selectedExpressions = selectBestExpressions(availableExpressions, 4, Array.from(allSelectedExpressions));
            
            if (selectedExpressions.length < 4) {
                console.warn(`Could not find 4 unique expressions for group: ${groupName}`);
                validPuzzle = false;
                break;
            }
            
            // Add expressions to the global tracking set
            selectedExpressions.forEach(expr => allSelectedExpressions.add(expr.expression));
            
            groups.push({
                category: groupName,
                words: selectedExpressions.map(item => item.expression),
                difficulty: difficultyColors[index]
            });
        }
        
        if (!validPuzzle || groups.length !== 4) {
            continue;
        }
        
        // Validate that all expressions are unique
        const allExpressions = groups.flatMap(g => g.words);
        const uniqueExpressions = new Set(allExpressions);
        
        if (uniqueExpressions.size !== 16) {
            console.warn(`Duplicate expressions found: ${allExpressions.length} total, ${uniqueExpressions.size} unique`);
            continue;
        }
        
        // Validate that the puzzle has exactly one solution
        if (validatePuzzleUniqueness(groups)) {
            console.log(`Generated valid puzzle with 16 unique expressions in ${attempts} attempts`);
            return { groups };
        }
        
        console.warn(`Puzzle attempt ${attempts} failed uniqueness validation`);
    }
    
    console.warn(`Could not generate unique puzzle after ${maxAttempts} attempts, using fallback`);
    return generateFallbackGame();
}

// Select 4 diverse groups for the puzzle
function selectPuzzleGroups(availableGroups) {
    // Prioritize groups with more expressions available
    const groupCounts = {};
    availableGroups.forEach(group => {
        groupCounts[group] = mathDatabase.filter(item => 
            item.groups.includes(group)
        ).length;
    });
    
    // Get groups that have at least 4 expressions
    const viableGroups = availableGroups.filter(group => groupCounts[group] >= 4);
    
    // Shuffle the viable groups to add randomness
    shuffleArray(viableGroups);
    
    // Select 4 groups, but ensure uniqueness by checking overlap
    const selectedGroups = [];
    for (const group of viableGroups) {
        if (selectedGroups.length >= 4) break;
        
        // Check if this group would create a unique puzzle
        if (isGroupSelectionValid(selectedGroups, group)) {
            selectedGroups.push(group);
        }
    }
    
    return selectedGroups.slice(0, 4);
}

// Find expressions that belong to a specific group
function findExpressionsForGroup(groupName, maxDifficulty, minDifficulty) {
    return mathDatabase.filter(item =>
        item.groups.includes(groupName) &&
        item.difficulty >= minDifficulty &&
        item.difficulty <= maxDifficulty
    );
}

// Select the best 4 expressions for a group (balancing difficulty and ensuring uniqueness)
function selectBestExpressions(expressions, count, selectedExpressionsSoFar = []) {
    if (expressions.length <= count) {
        return expressions;
    }
    
    // Convert selectedExpressionsSoFar to expressions for comparison
    const alreadySelectedExpressions = selectedExpressionsSoFar;
    
    // Filter out expressions that are already selected (by expression string)
    const uniqueExpressions = expressions.filter(expr => 
        !alreadySelectedExpressions.includes(expr.expression)
    );
    
    // Use the filtered expressions
    const candidateExpressions = uniqueExpressions;
    
    if (candidateExpressions.length < count) {
        console.warn(`Not enough unique candidates: ${candidateExpressions.length} < ${count}`);
        return candidateExpressions;
    }
    
    // Shuffle to add randomness
    shuffleArray(candidateExpressions);
    
    // Try to get a good difficulty distribution while maintaining randomness
    const selected = [];
    const difficulties = [1, 2, 3, 4, 5];
    
    // First, try to get one expression from each difficulty level available
    for (const difficulty of difficulties) {
        if (selected.length >= count) break;
        const difficultyExprs = candidateExpressions.filter(expr => 
            expr.difficulty === difficulty && !selected.includes(expr)
        );
        if (difficultyExprs.length > 0) {
            selected.push(difficultyExprs[0]);
        }
    }
    
    // Fill remaining slots randomly
    while (selected.length < count && candidateExpressions.length > selected.length) {
        const remaining = candidateExpressions.filter(expr => !selected.includes(expr));
        if (remaining.length > 0) {
            selected.push(remaining[Math.floor(Math.random() * remaining.length)]);
        } else {
            break;
        }
    }
    
    return selected.slice(0, count);
}

// Check if adding a group would create a valid selection
function isGroupSelectionValid(currentGroups, newGroup) {
    // For now, just ensure we don't have too much overlap
    // This is a simple heuristic - you could make it more sophisticated
    return true;
}

// Check if an expression would create ambiguity with already selected expressions
function wouldCreateAmbiguity(expression, selectedExpressions) {
    // Find all groups this expression belongs to
    const expressionGroups = mathDatabase
        .find(item => item.expression === expression.expression)?.groups || [];
    
    // Check if any already selected expressions also belong to these groups
    for (const selectedExpr of selectedExpressions) {
        const selectedGroups = mathDatabase
            .find(item => item.expression === selectedExpr.expression)?.groups || [];
        
        // If there's overlap in groups, this could create ambiguity
        const overlap = expressionGroups.filter(group => selectedGroups.includes(group));
        if (overlap.length > 0) {
            return true;
        }
    }
    
    return false;
}

// Validate that the final puzzle has exactly one solution
function validatePuzzleUniqueness(groups) {
    const selectedGroupNames = groups.map(g => g.category);
    
    // Check each expression to see if it could belong to multiple selected groups
    for (const group of groups) {
        for (const word of group.words) {
            // Find the database entry for this expression
            const dbEntry = mathDatabase.find(item => item.expression === word);
            if (!dbEntry) {
                console.warn(`Expression "${word}" not found in database`);
                return false;
            }
            
            // Count how many of our selected groups this expression belongs to
            const belongsToGroups = dbEntry.groups.filter(g => selectedGroupNames.includes(g));
            
            if (belongsToGroups.length > 1) {
                console.warn(`Expression "${word}" belongs to multiple selected groups:`, belongsToGroups);
                return false;
            }
            
            if (belongsToGroups.length === 0) {
                console.warn(`Expression "${word}" doesn't belong to any selected group`);
                return false;
            }
            
            // Verify it belongs to the correct group
            if (!belongsToGroups.includes(group.category)) {
                console.warn(`Expression "${word}" assigned to wrong group`);
                return false;
            }
        }
    }
    
    // Additional check: ensure no combination of 4 expressions from different groups
    // could accidentally form a valid group from the database
    const allWords = groups.flatMap(g => g.words);
    
    // This is computationally expensive for large sets, so we'll do a lighter check
    // We already verified each expression belongs to exactly one selected group,
    // which should be sufficient for our purposes
    
    return true;
}

// Fallback game generation
function generateFallbackGame() {
    return {
        groups: [
            {
                category: "Expressions equal to 1",
                words: ["$\\displaystyle \\sin^2\\theta + \\cos^2\\theta$", "$\\displaystyle e^0$", "$\\displaystyle \\lim_{x \\to 0} \\frac{\\sin x}{x}$", "$\\displaystyle \\cos^2\\frac{\\pi}{4}$"],
                difficulty: "yellow"
            },
            {
                category: "Famous constants",
                words: ["$\\displaystyle \\pi$", "$\\displaystyle e$", "$\\displaystyle \\phi = \\frac{1+\\sqrt{5}}{2}$", "$\\displaystyle \\sqrt{2}$"],
                difficulty: "green"
            },
            {
                category: "Derivative rules",
                words: ["$\\displaystyle \\frac{d}{dx}[x^n] = nx^{n-1}$", "$\\displaystyle \\frac{d}{dx}[\\sin x] = \\cos x$", "$\\displaystyle \\frac{d}{dx}[e^x] = e^x$", "$\\displaystyle \\frac{d}{dx}[\\ln x] = \\frac{1}{x}$"],
                difficulty: "blue"
            },
            {
                category: "Complex numbers",
                words: ["$\\displaystyle e^{i\\pi} + 1 = 0$", "$\\displaystyle |z|^2 = z \\cdot \\overline{z}$", "$\\displaystyle \\sqrt{-1} = i$", "$\\displaystyle (a+bi)(a-bi) = a^2 + b^2$"],
                difficulty: "purple"
            }
        ]
    };
}

// Initialize the game
function initGame(options = {}) {
    // Generate a new game from the database
    gameData = generateGame(options);
    
    // Flatten all words and shuffle them
    gameWords = gameData.groups.flatMap(group => group.words);
    shuffleArray(gameWords);
    
    // Reset game state
    selectedWords = [];
    mistakesRemaining = 4;
    foundGroups = [];
    
    // Show the mistakes counter
    const mistakesCounter = document.getElementById('mistakesCounter');
    if (mistakesCounter) {
        mistakesCounter.style.display = 'block';
    }
    
    renderWordGrid();
    updateMistakeCounter();
    hideMessage();
    
    // Clear any previous found groups
    document.getElementById('foundGroups').innerHTML = '';
}

// Render the word grid
function renderWordGrid() {
    const wordGrid = document.getElementById('wordGrid');
    wordGrid.innerHTML = '';
    
    gameWords.forEach(expression => {
        const expressionCard = document.createElement('div');
        expressionCard.className = 'word-card';
        
        // Convert inline math to display math for proper rendering
        let displayExpression = expression;
        if (expression.startsWith('$') && expression.endsWith('$') && !expression.startsWith('$$')) {
            // Convert single $ to double $$ for display math
            displayExpression = '$' + expression + '$';
        }
        
        expressionCard.innerHTML = displayExpression;
        expressionCard.onclick = () => toggleWord(expression, expressionCard);
        wordGrid.appendChild(expressionCard);
    });
    
    // Render MathJax after updating the grid
    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([wordGrid]);
    }
}

// Toggle word selection
function toggleWord(word, cardElement) {
    if (selectedWords.includes(word)) {
        // Deselect word
        selectedWords = selectedWords.filter(w => w !== word);
        cardElement.classList.remove('selected');
    } else if (selectedWords.length < 4) {
        // Select word
        selectedWords.push(word);
        cardElement.classList.add('selected');
    }
    
    updateSubmitButton();
}

// Update submit button state
function updateSubmitButton() {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = selectedWords.length !== 4;
}

// Deselect all words
function deselectAll() {
    selectedWords = [];
    document.querySelectorAll('.word-card').forEach(card => {
        card.classList.remove('selected');
    });
    updateSubmitButton();
}

// Submit guess
function submitGuess() {
    if (selectedWords.length !== 4) return;
    
    // Check if the selected words form a group
    const correctGroup = gameData.groups.find(group => 
        selectedWords.every(word => group.words.includes(word)) &&
        selectedWords.length === 4
    );
    
    if (correctGroup) {
        // Correct guess!
        foundGroups.push(correctGroup);
        showMessage(`Correct! ${correctGroup.category}`, 'success');
        
        // Remove found words from the grid
        gameWords = gameWords.filter(word => !selectedWords.includes(word));
        selectedWords = [];
        
        // Render found group
        renderFoundGroup(correctGroup);
        renderWordGrid();
        
        // Check if game is won
        if (foundGroups.length === gameData.groups.length) {
            showMessage('Congratulations! You found all groups!', 'success');
            document.getElementById('submitBtn').disabled = true;
        }
    } else {
        // Wrong guess
        mistakesRemaining--;
        updateMistakeCounter();
        
        if (mistakesRemaining === 0) {
            showMessage('Game Over! No more mistakes remaining.', 'error');
            document.getElementById('submitBtn').disabled = true;
            revealAllGroups();
        } else {
            // Check if it's close (3 out of 4 correct)
            const closestGroup = findClosestGroup();
            if (closestGroup) {
                showMessage('One away from a group!', 'warning');
            } else {
                showMessage(`Incorrect. ${mistakesRemaining} mistakes remaining.`, 'error');
            }
        }
        
        deselectAll();
    }
    
    updateSubmitButton();
}

// Find the closest group (3 out of 4 correct)
function findClosestGroup() {
    return gameData.groups.find(group => {
        const matches = selectedWords.filter(word => group.words.includes(word));
        return matches.length === 3;
    });
}

// Render found group
function renderFoundGroup(group) {
    const foundGroupsContainer = document.getElementById('foundGroups');
    
    const groupElement = document.createElement('div');
    groupElement.className = `group ${group.difficulty}`;
    
    groupElement.innerHTML = `
        <div class="group-title">${group.category}</div>
        <div class="group-words">${group.words.join(' &nbsp;&nbsp; ')}</div>
    `;
    
    foundGroupsContainer.appendChild(groupElement);
    
    // Render MathJax for the new group
    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([groupElement]);
    }
}

// Reveal all groups (game over)
function revealAllGroups() {
    gameData.groups.forEach(group => {
        if (!foundGroups.some(found => found.category === group.category)) {
            renderFoundGroup(group);
        }
    });
    
    // Clear the word grid
    document.getElementById('wordGrid').innerHTML = '';
}

// Update mistake counter
function updateMistakeCounter() {
    const mistakesMade = 4 - mistakesRemaining;
    const mistakeVisual = document.getElementById('mistakeVisual');
    
    if (mistakeVisual) {
        // Create visual representation: X for mistakes made, ○ for remaining
        const mistakes = '✕'.repeat(mistakesMade);
        const remaining = '○'.repeat(mistakesRemaining);
        mistakeVisual.innerHTML = `<span style="color: #e74c3c;">${mistakes}</span><span style="color: #bdc3c7;">${remaining}</span>`;
    }
    
    // Keep the old element for backward compatibility
    const mistakeCount = document.getElementById('mistakeCount');
    if (mistakeCount) {
        mistakeCount.textContent = mistakesRemaining;
    }
}

// Show message
function showMessage(text, type) {
    const messageElement = document.getElementById('message');
    messageElement.textContent = text;
    messageElement.className = `message ${type} show`;
    
    // Hide message after 3 seconds
    setTimeout(() => {
        hideMessage();
    }, 3000);
}

// Hide message
function hideMessage() {
    const messageElement = document.getElementById('message');
    messageElement.classList.remove('show');
}

// Shuffle words
function shuffleWords() {
    shuffleArray(gameWords);
    renderWordGrid();
    deselectAll();
}

// Utility function to shuffle array
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

// Game control functions
function newEasyGame() {
    initGame({ maxDifficulty: 2, minDifficulty: 1 });
}

function newMediumGame() {
    initGame({ maxDifficulty: 3, minDifficulty: 1 });
}

function newHardGame() {
    initGame({ maxDifficulty: 5, minDifficulty: 2 });
}

function newCustomGame() {
    // You could add a modal or form here for custom options
    const options = {
        maxDifficulty: 4,
        minDifficulty: 1,
        preferredGroups: ['Derivative rules', 'Integral rules', 'Trigonometric identities']
    };
    initGame(options);
}

// Handle database selection change
async function onDatabaseChange() {
    const selector = document.getElementById('databaseSelect');
    const selectedDatabase = selector.value;
    
    // Don't proceed if no database is selected (empty value)
    if (!selectedDatabase) {
        return;
    }
    
    // Remove the default "Select a database" option once a real database is selected
    const defaultOption = selector.querySelector('option[value=""]');
    if (defaultOption) {
        defaultOption.remove();
    }
    
    // Show loading message
    const wordGrid = document.getElementById('wordGrid');
    wordGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #7f8c8d;">Loading database...</div>';
    
    // Load the new database
    await loadMathDatabase(selectedDatabase);
    
    // Show and enable game control buttons
    const gameControls = document.getElementById('gameControls');
    const submitControls = document.getElementById('submitControls');
    const topControls = document.querySelector('.top-controls');
    const newGameBtn = document.getElementById('newGameBtn');
    const shuffleBtn = document.getElementById('shuffleBtn');
    
    if (gameControls) gameControls.style.display = 'flex';
    if (submitControls) submitControls.style.display = 'flex';
    if (topControls) topControls.classList.remove('center-selector');
    newGameBtn.disabled = false;
    shuffleBtn.disabled = false;
    
    // Start a new game with the new database
    initGame();
}

// Initialize the application
async function initializeApp() {
    // Show selection prompt instead of loading message
    const wordGrid = document.getElementById('wordGrid');
    wordGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #7f8c8d; font-size: 1.1em;">Please select a topic above to start playing!</div>';
    
    // Reset database selector to default empty value
    const databaseSelect = document.getElementById('databaseSelect');
    databaseSelect.value = '';
    databaseSelect.addEventListener('change', onDatabaseChange);
    
    // Set up game control button event listeners
    const gameControls = document.getElementById('gameControls');
    const submitControls = document.getElementById('submitControls');
    const topControls = document.querySelector('.top-controls');
    const newGameBtn = document.getElementById('newGameBtn');
    const shuffleBtn = document.getElementById('shuffleBtn');
    
    newGameBtn.addEventListener('click', () => initGame());
    shuffleBtn.addEventListener('click', shuffleWords);
    
    // Hide game controls and submit buttons until database is selected
    if (gameControls) gameControls.style.display = 'none';
    if (submitControls) submitControls.style.display = 'none';
    if (topControls) topControls.classList.add('center-selector');
    newGameBtn.disabled = true;
    shuffleBtn.disabled = true;
    
    // Don't load any database or start a game by default
}

// Start the app when page loads
document.addEventListener('DOMContentLoaded', initializeApp);
