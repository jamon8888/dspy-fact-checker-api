// content.js
console.log("Fact-Checker ChatGPT Extension content script loaded.");

// Style Constants
const BUTTON_STYLE = `
  width: 1.5rem; /* size-6 */
  height: 1.5rem; /* size-6 */
  border-radius: 9999px; /* rounded-full */
  border: 5px dashed black; /* border-5 border-black border-dashed */
  background-color: white;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  cursor: pointer;
  color: black; /* Fallback for icon color if not set by SVG */
  position: relative; /* Needed for tooltip positioning if tooltip is child */
`;

const TOOLTIP_STYLE = `
  position: absolute;
  bottom: 100%; /* Position above the button */
  left: 50%;
  transform: translateX(-50%) translateY(5px); /* Initial position for animation */
  background-color: #333; /* Dark background like some Apple tooltips */
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease-in-out, transform 0.2s ease-in-out, visibility 0.2s ease-in-out;
  z-index: 10; /* Ensure it's above other elements */
  margin-bottom: 8px; /* Space between button and tooltip */
`;

// Helper function to get trimmed text from an element
function getElementText(element) {
  if (!element) return "";
  return (element.innerText || element.textContent || "").trim();
}

function addFloatingButtonToMessage(assistantMessageDiv) {
  const messageTurnRoot = assistantMessageDiv.closest(
    ".group.conversation-turn"
  );
  if (messageTurnRoot?.querySelector(".fact-checker-btn")) {
    return;
  }

  const button = document.createElement("button");
  button.className = "fact-checker-btn";
  button.title = "Check Fact";

  // SVG Logo (Checkmark)
  button.innerHTML =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width: 12px; height: 12px; display: block;" fill="none" stroke="black" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17L4 12"/></svg>';

  // Apply requested styles
  button.style.cssText = BUTTON_STYLE;

  // Create a container for the button and tooltip
  const buttonContainer = document.createElement("div");
  buttonContainer.style.position = "relative";
  buttonContainer.style.display = "inline-block"; // Or 'flex' if needed for alignment

  // Create tooltip element
  const tooltip = document.createElement("span");
  tooltip.innerText = "Fact Check";
  tooltip.style.cssText = TOOLTIP_STYLE;
  buttonContainer.appendChild(tooltip);
  buttonContainer.appendChild(button);

  // Show tooltip on hover
  buttonContainer.onmouseenter = () => {
    tooltip.style.opacity = "1";
    tooltip.style.visibility = "visible";
    tooltip.style.transform = "translateX(-50%) translateY(0)";
  };

  buttonContainer.onmouseleave = () => {
    tooltip.style.opacity = "0";
    tooltip.style.visibility = "hidden";
    tooltip.style.transform = "translateX(-50%) translateY(5px)";
  };

  button.onclick = () => {
    // Extract Assistant's Text
    const assistantMarkdownContent =
      assistantMessageDiv.querySelector(".markdown.prose");
    let assistantText = getElementText(assistantMarkdownContent);

    if (!assistantText) {
      assistantText = getElementText(assistantMessageDiv);
      if (assistantText) {
        console.warn(
          "Could not find '.markdown.prose' in assistant message, falling back to full message content:",
          assistantMessageDiv
        );
      } else {
        console.error(
          "Could not extract assistant's text from message (tried .markdown.prose and full div):",
          assistantMessageDiv
        );
        return; // No assistant text, nothing to do
      }
    }

    // Extract last User's Text
    let userText = "(User prompt not found)"; // Default if not found
    const currentArticle = assistantMessageDiv.closest(
      'article[data-testid^="conversation-turn-"]'
    );
    if (currentArticle) {
      const previousArticle = currentArticle.previousElementSibling;
      if (
        previousArticle?.matches('article[data-testid^="conversation-turn-"]')
      ) {
        const userMessageDiv = previousArticle.querySelector(
          'div[data-message-author-role="user"]'
        );
        if (userMessageDiv) {
          const userTextContentDiv = userMessageDiv.querySelector(
            'div[class*="whitespace-pre-wrap"]'
          );
          const extractedUserText =
            getElementText(userTextContentDiv) ||
            getElementText(userMessageDiv);
          if (extractedUserText) {
            userText = extractedUserText;
            if (!userTextContentDiv) {
              console.warn(
                "Could not find specific text content div in user message, using full user div text.",
                userMessageDiv
              );
            }
          } else {
            console.warn(
              "User message div found, but no text could be extracted.",
              userMessageDiv
            );
          }
        }
      }
    }

    // No need to check if (assistantText) here because we return early if it's empty
    const encodedAssistantText = encodeURIComponent(assistantText); // Already trimmed by getElementText
    const encodedUserText = encodeURIComponent(userText); // Already trimmed by getElementText or default value
    const redirectUrl = `http://localhost:3000/?q=${encodedUserText}&a=${encodedAssistantText}`;
    window.open(redirectUrl, "_blank");
  };

  let actionsToolbarEl = null;
  const messageBlockParent = assistantMessageDiv.closest(
    ".relative.flex-col.gap-1"
  );
  if (messageBlockParent) {
    actionsToolbarEl = messageBlockParent.querySelector(".flex.justify-start");
  }

  if (actionsToolbarEl) {
    actionsToolbarEl.appendChild(buttonContainer); // Append container instead of button
    console.log(
      "Fact-checker button with tooltip added to actions toolbar:",
      actionsToolbarEl
    );
  } else {
    console.warn(
      "Could not find specific actions toolbar, appending button with tooltip directly to message element (fallback).",
      assistantMessageDiv
    );
    assistantMessageDiv.appendChild(buttonContainer); // Append container instead of button
  }
  console.log(
    "Fact-checker button added to (or attempted for):",
    assistantMessageDiv
  );
}

function processAssistantMessage(assistantMessageDiv) {
  const messageTurnRoot = assistantMessageDiv.closest(
    ".group.conversation-turn"
  );
  if (messageTurnRoot?.querySelector(".fact-checker-btn")) {
    // Button already exists for this message turn
    return;
  }

  const markdownDiv = assistantMessageDiv.querySelector(".markdown.prose");

  if (markdownDiv) {
    if (!markdownDiv.classList.contains("streaming-animation")) {
      console.log("Message complete, adding button:", assistantMessageDiv);
      addFloatingButtonToMessage(assistantMessageDiv);
    } else {
      console.log("Message streaming, observing for completion:", markdownDiv);
      const streamingObserver = new MutationObserver(
        (mutationsList, observer) => {
          for (const mutation of mutationsList) {
            if (
              mutation.type === "attributes" &&
              mutation.attributeName === "class"
            ) {
              if (!mutation.target.classList.contains("streaming-animation")) {
                console.log(
                  "Streaming finished, adding button:",
                  assistantMessageDiv
                );
                addFloatingButtonToMessage(assistantMessageDiv);
                observer.disconnect();
                break;
              }
            }
          }
        }
      );
      streamingObserver.observe(markdownDiv, {
        attributes: true,
        attributeFilter: ["class"],
      });
    }
  } else {
    console.warn(
      "Could not find '.markdown.prose' child in assistant message for streaming check:",
      assistantMessageDiv
    );
    addFloatingButtonToMessage(assistantMessageDiv);
  }
}

function observeOverallMessages() {
  const assistantMessageSelector = 'div[data-message-author-role="assistant"]';

  const mainObserver = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          if (node.matches(assistantMessageSelector)) {
            processAssistantMessage(node);
          }
          node
            .querySelectorAll(assistantMessageSelector)
            .forEach(processAssistantMessage);
        }
      }
    }
  });

  mainObserver.observe(document.body, { childList: true, subtree: true });
  document
    .querySelectorAll(assistantMessageSelector)
    .forEach(processAssistantMessage);
}

observeOverallMessages();
