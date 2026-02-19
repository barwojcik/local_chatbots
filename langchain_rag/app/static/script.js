// Constants and state management
const STATE = {
    isFirstMessage: true,
    responses: [],
    baseUrl: window.location.origin,
    isProcessing: false
};

// Object to store model data from server
let modelData = {
    availableModels: ['Add a model'],
    currentModel: null
};

// Utility functions
const sleep = (time) => new Promise((resolve) => setTimeout(resolve, time));

const cleanTextInput = (value) => {
    return value
        .trim()
        .replace(/[\n\t]/g, "")
        .replace(/<[^>]*>/g, "")
        .replace(/[<>&;]/g, "");
};

// UI manipulation functions
const showBotLoadingAnimation = async () => {
    if (STATE.isProcessing) return;
    STATE.isProcessing = true;
    await sleep(200);
    $('.loading-animation').last().fadeIn(100);
    $('#send-button').prop('disabled', true);
};

const hideBotLoadingAnimation = () => {
    STATE.isProcessing = false;
    $('.loading-animation').last().hide();
    if (!STATE.isFirstMessage) {
        $('#send-button').prop('disabled', false);
    }
};

const scrollToBottom = () => {
    const chatWindow = $('#chat-window');
    chatWindow.animate({
        scrollTop: chatWindow[0].scrollHeight
    }, 300);
};

// API interaction functions
const processUserMessage = async (userMessage) => {
    try {
        const response = await fetch(`${STATE.baseUrl}/messages`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ userMessage })
        });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('User message processed:', data);
        return data;
    } catch (error) {
        console.error('Error processing user message:', error);
        showErrorMessage('Failed to process message. Please try again.');
        return null;
    }
};

const resetBotChatHistory = async () => {
    try {
        const response = await fetch('/reset-chat-history', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Chat history reset successfully:', data);
        return data;
    } catch (error) {
        console.error('Error resetting chat history:', error);
        showErrorMessage('Failed to reset chat history. Please try again.');
        return null;
    }
};

const resetVectorStore = async () => {
    try {
        const response = await fetch('/reset-vector-store', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Vector store reset successfully:', data);
        return data;
    } catch (error) {
        console.error('Error resetting vector store:', error);
        showErrorMessage('Failed to reset uploaded file context. Please try again.');
        return null;
    }
};

// Message handling functions
const showErrorMessage = (message) => {
    hideBotLoadingAnimation();

    $('#message-list').append(`
        <div class="message-line error">
            <div class="message-box error">
                ${message}
            </div>
        </div>
    `);
    scrollToBottom();
};

const populateUserMessage = (userMessage) => {
    $('#message-input').val('');
    $('#message-list').append(`
        <div class="message-line my-text">
            <div class="message-box my-text">
                <div class="me">${userMessage}</div>
            </div>
        </div>
    `);
    scrollToBottom();
};

const renderBotResponse = (response) => {
    if (!response) return;

    STATE.responses.push(response);
    hideBotLoadingAnimation();

    // Parse markdown if the marked library is available
    let formattedResponse;
    if (typeof marked !== 'undefined') {
        // Set marked options to safely handle user-generated content
        marked.setOptions({
            breaks: true,        // Add line breaks when \n is encountered
            gfm: true,           // Use GitHub Flavored Markdown
            headerIds: false,    // Don't add IDs to headers (for security)
            sanitize: false,     // Required for compatibility, we'll sanitize elsewhere
            highlight: function(code, lang) {
                // Apply syntax highlighting if highlight.js is available
                if (typeof hljs !== 'undefined') {
                    if (lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (err) {
                            console.error('Highlight.js error:', err);
                        }
                    }
                    try {
                        return hljs.highlightAuto(code).value;
                    } catch (err) {
                        console.error('Highlight.js auto-detection error:', err);
                    }
                }
                return code; // Return unmodified code if highlighting fails
            }
        });

        formattedResponse = marked.parse(response.botResponse.trim());
    } else {
        formattedResponse = response.botResponse.trim();
    }

    $('#message-list').append(`
        <div class="message-line">
            <div class="message-box markdown-content">
                ${formattedResponse}
            </div>
        </div>
    `);

    // Apply additional highlighting to any code blocks that might have been missed
    if (typeof hljs !== 'undefined') {
        $('pre code').each(function(i, block) {
            if (!block.classList.contains('hljs')) {
                hljs.highlightElement(block);
            }
        });
    }

    scrollToBottom();
};

const handleUserMessage = async () => {
    const messageInput = $('#message-input');
    const message = cleanTextInput(messageInput.val());

    if (!message || STATE.isProcessing) return;

    populateUserMessage(message);
    await populateBotResponse(message);
};

const populateBotResponse = async (userMessage) => {
    await showBotLoadingAnimation();

    let response;
    if (STATE.isFirstMessage) {
        response = {
            botResponse: "Hello there! I'm your friendly AI assistant, ready to chat! Upload a file if you want to add any context."
        };
        STATE.isFirstMessage = false;
        renderBotResponse(response);
    }
    if (userMessage){
        response = await processUserMessage(userMessage);
        renderBotResponse(response);
    }
    hideBotLoadingAnimation();
};

// Function to fetch history data from server
async function fetchHistoryData() {
    try {
        const response = await fetch('/messages');
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        let msg;
        const data = await response.json();
        if (data.status === 'success'){
            if (data.messages.length > 0){
                data.messages.forEach((message) => {
                    if (message.role === 'user'){
                        populateUserMessage(message.content)
                    }
                    if (message.role === 'assistant'){
                        msg = {
                            botResponse: message.content
                        };
                        renderBotResponse(msg);
                    }
                })
                STATE.isFirstMessage = false;
            }
        }
    } catch (error) {
        console.error('Error fetching history data:', error);
    }
}

// Function to fetch model data from server
async function fetchModelData() {
    try {
        const response = await fetch('/model');
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        modelData.availableModels = data.available_models || [];
        modelData.currentModel = data.current_model || '';

        // Update model selection dropdown
        updateModelSelector();
    } catch (error) {
        console.error('Error fetching model data:', error);
    }
}

// Function to update the model selector dropdown
function updateModelSelector() {
    const modelSelect = document.getElementById('modelSelect');

    // Clear existing options
    modelSelect.innerHTML = '';

    // Add options for each available model
    modelData.availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        if (model === modelData.currentModel) {
            option.selected = true;
        }
        modelSelect.appendChild(option);
    });
}

// Function to set the current model
async function setCurrentModel(modelName) {
    try {
        const response = await fetch('/model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: modelName
            })
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
            modelData.currentModel = modelName;
            console.log(`Model successfully set to: ${modelName}`);
                return true; // Return success status
            } else {
                const errorMsg = data.error || 'Unknown error';
                console.error(`Failed to set model: ${errorMsg}`);
                throw new Error(errorMsg);
            }
        } catch (error) {
            console.error('Error setting model:', error);
            throw error; // Re-throw to allow caller to handle
    }
}

// Document ready handler
$(document).ready(() => {
    // Initial setup
    $('#send-button').prop('disabled', true);

    // Event handlers
    $('#message-input').on('keyup', async (event) => {
        const inputVal = cleanTextInput($(event.target).val());
        if (event.keyCode === 13 && inputVal) {
            await handleUserMessage();
        }
    });

    $("#upload-button").on("click", () => {
        $("#file-upload").click();
    });

    $("#file-upload").on("change", async function () {
        try {
            await showBotLoadingAnimation();

            const formData = new FormData();
            let i = 1;
            for (const file of this.files) { // Accessing files directly from this.files
                if (file.type.includes('pdf')) {
                    formData.append(`file${i}`, file);
                    i++;
                }
            }

            if (formData.length === 0) {
                throw new Error("Please select at least one valid file");
            }

            const response = await fetch(`${STATE.baseUrl}/document`, {
                method: "POST",
                headers: { Accept: "application/json" },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed with status: ${response.status}`);
            }

            const responseData = await response.json();
            console.log('/document', responseData);
            renderBotResponse(responseData, '');

        } catch (error) {
            console.error('File upload error:', error);
            showErrorMessage(error.message);
        }
    });

    $('#send-button').on('click', handleUserMessage);

    $('#reset-button').on('click', async () => {
        $('#message-list').empty();
        STATE.responses = [];
        STATE.isFirstMessage = true;
        await resetBotChatHistory();
        await resetVectorStore();
        await populateBotResponse();
    });

    // Add event listener for model selection changes
    document.getElementById('modelSelect').addEventListener('change', function() {
        const selectedModel = this.value;
        if (selectedModel && selectedModel !== modelData.currentModel) {
            setCurrentModel(selectedModel);
        }
    });

    // Start the chat
    fetchModelData();
    fetchHistoryData();
    populateBotResponse();
});
