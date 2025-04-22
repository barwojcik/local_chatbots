let lightMode = true;
const responses = [];
const baseUrl = window.location.origin

async function showBotLoadingAnimation() {
  await sleep(200);
  $(".loading-animation")[1].style.display = "inline-block";
  document.getElementById('send-button').disabled = true;
}

function hideBotLoadingAnimation() {
  $(".loading-animation")[1].style.display = "none";
  if(!isFirstMessage){
    document.getElementById('send-button').disabled = false;
  }
}

const processUserMessage = async (userMessage) => {
  try {
    let response = await fetch(baseUrl + "/process-message", {
      method: "POST",
      headers: {Accept: "application/json", "Content-Type": "application/json"},
      body: JSON.stringify({userMessage: userMessage}),
    });
    if (!response.ok) {
      const message = `Error while processing user message: ${response.status} ${response.statusText}`;
      throw new Error(message);
    }
    response = await response.json();
    console.log("User message processed:", response);
    return response;
  } catch (error) {
    console.error("Error processing user message:", error);
    return null;
  }
};

const resetBotChatHistory = async () => {
  try {
    let response = await fetch('/reset-chat-history', {
      method: "GET",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    if (!response.ok) {
      const message = `Error resetting chat history: ${response.status} ${response.statusText}`;
      throw new Error(message);
    }
    response = await response.json();
    console.log("Chat history reset successfully:", response);
    return response;
  } catch (error) {
    console.error("Error resetting chat history:", error);
    return null;
  }
};

const resetVectorStore = async () => {
  try {
    let response = await fetch('/reset-vector-store', {
      method: "GET",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    if (!response.ok) {
      const message = `Error resetting vector store: ${response.status} ${response.statusText}`;
      throw new Error(message);
    }
    response = await response.json();
    console.log("Vector store reset successfully:", response);
    return response;
  } catch (error) {
    console.error("Error resetting vector store:", error);
    return null;
  }
};

const cleanTextInput = (value) => {
  return value
    .trim() // remove starting and ending spaces
    .replace(/[\n\t]/g, "") // remove newlines and tabs
    .replace(/<[^>]*>/g, "") // remove HTML tags
    .replace(/[<>&;]/g, ""); // sanitize inputs
};

const sleep = (time) => new Promise((resolve) => setTimeout(resolve, time));

const scrollToBottom = () => {
  // Scroll the chat window to the bottom
  $("#chat-window").animate({
    scrollTop: $("#chat-window")[0].scrollHeight,
  });
};

const populateUserMessage = (userMessage, userRecording) => {
  // Clear the input field
  $("#message-input").val("");

  // Append the user's message to the message list
    $("#message-list").append(
      `<div class='message-line my-text'><div class='message-box my-text${
        !lightMode ? " dark" : ""
      }'><div class='me'>${userMessage}</div></div></div>`
    );

  scrollToBottom();
};

let isFirstMessage = true;

const populateBotResponse = async (userMessage) => {
  await showBotLoadingAnimation();

  let response;
  let uploadButtonHtml = '';

  if (isFirstMessage) {
    response = { botResponse: "Hello there! I'm your friendly data assistant, ready to answer any questions regarding your data. Could you please upload a PDF file for me to analyze?"};
    uploadButtonHtml = `
        <input type="file" id="file-upload" accept=".pdf" hidden>
        <button id="upload-button" class="btn btn-primary btn-sm">Upload File</button>
    `;

  } else {
    response = await processUserMessage(userMessage);
  }

  renderBotResponse(response, uploadButtonHtml)

  // Event listener for file upload
  if (isFirstMessage) {
    $("#upload-button").on("click", function () {
      $("#file-upload").click();
    });

    $("#file-upload").on("change", async function () {
      const file = this.files[0];

      await showBotLoadingAnimation();

      // Create a new FormData instance
      const formData = new FormData();

      // Append the file to the FormData instance
      formData.append('file', file);

      // Now send this data to /process-document endpoint
      let response = await fetch(baseUrl + "/process-document", {
        method: "POST",
        headers: { Accept: "application/json" }, // "Content-Type" should not be explicitly set here, the browser will automatically set it to "multipart/form-data"
        body: formData, // send the FormData instance as the body
      });

      if (response.status !== 400) {
           document.querySelector('#upload-button').disabled = true;
      }

      response = await response.json();
      console.log('/process-document', response)
      renderBotResponse(response, '')
    });


    isFirstMessage = false; // after the first message, set this to false
  }
};

const renderBotResponse = (response, uploadButtonHtml) => {
  responses.push(response);

  hideBotLoadingAnimation();

  $("#message-list").append(
    `<div class='message-line'><div class='message-box${!lightMode ? " dark" : ""}'>${response.botResponse.trim()}<br>${uploadButtonHtml}</div></div>`
  );

  scrollToBottom();
}

populateBotResponse()


$(document).ready(function () {

  //start the chat with send button disabled
  document.getElementById('send-button').disabled = true;

  // Listen for the "Enter" key being pressed in the input field
  $("#message-input").keyup(function (event) {
    let inputVal = cleanTextInput($("#message-input").val());

    if (event.keyCode === 13 && inputVal != "") {
      const message = inputVal;

      populateUserMessage(message, null);
      populateBotResponse(message);
    }

    inputVal = $("#message-input").val();
  });

  // When the user clicks the "Send" button
  $("#send-button").click(async function () {
  // Get the message the user typed in
  const message = cleanTextInput($("#message-input").val());

  populateUserMessage(message, null);
  populateBotResponse(message);

  });

  //reset chat
  // When the user clicks the "Reset" button
  $("#reset-button").click(async function () {
    // Clear the message list
    $("#message-list").empty();

    // Reset the response array
    responses.length = 0;

    // Reset isFirstMessage flag
    isFirstMessage = true;

    // Reset the chat history
    resetBotChatHistory()

    // Reset the vector store
    resetVectorStore()

    document.querySelector('#upload-button').disabled = false;

    // Start over
    populateBotResponse();
  });


  // handle the event of switching light-dark mode
  $("#light-dark-mode-switch").change(function () {
    $("body").toggleClass("dark-mode");
    $(".message-box").toggleClass("dark");
    $(".loading-dots").toggleClass("dark");
    $(".dot").toggleClass("dark-dot");
    lightMode = !lightMode;
  });
});
