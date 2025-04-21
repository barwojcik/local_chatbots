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

  if (isFirstMessage) {
    response = { botResponse: "Hello there! I'm your friendly LLM, ready to chat just about anything!"};
  } else {
    response = await processUserMessage(userMessage);
  }

  renderBotResponse(response)

  if (isFirstMessage) {
    isFirstMessage = false; // after the first message, set this to false
  }
};

const renderBotResponse = (response) => {
  responses.push(response);

  hideBotLoadingAnimation();

  $("#message-list").append(
    `<div class='message-line'><div class='message-box${!lightMode ? " dark" : ""}'>${response.botResponse.trim()}</div></div>`
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
      await resetBotChatHistory()

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
