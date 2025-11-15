// Replace with your ngrok URL
const API_URL = "https://hairlike-unhopefully-maude.ngrok-free.dev/predict";

// Keep track of last processed email to avoid repeated overlay
let lastEmailId = null;

function getEmailContent() {
  // Improved selectors with fallbacks for subject (Gmail's DOM can vary)
  const subjectSelectors = ['h2.hP', 'h2[data-thread-perm-id]', 'h2[role="heading"]'];
  let subjectEl = null;
  for (const selector of subjectSelectors) {
    subjectEl = document.querySelector(selector);
    if (subjectEl) break;
  }

  // Improved selectors with fallbacks for body
  const bodySelectors = ['div.a3s', 'div[aria-label*="Message body"]', 'div.nH div.a3s'];
  let bodyEl = null;
  for (const selector of bodySelectors) {
    bodyEl = document.querySelector(selector);
    if (bodyEl) break;
  }

  if (!subjectEl || !bodyEl) {
    console.log("Email content not found. Tried subject selectors:", subjectSelectors, "body selectors:", bodySelectors);
    return null;
  }

  const subject = subjectEl.innerText || subjectEl.textContent;
  const body = bodyEl.innerText || bodyEl.textContent;
  // Fallback for emailId if attribute is missing; combine with subject for uniqueness
  const threadId = subjectEl.getAttribute('data-thread-perm-id') || subjectEl.getAttribute('data-legacy-thread-id') || 'unknown';
  const emailId = `${threadId}-${subject.substring(0, 20)}`; // Make it unique per email

  console.log("Detected email - ID:", emailId, "Subject:", subject.substring(0, 50) + "...");
  return { subject, body, emailId, bodyEl };
}

async function checkSpam(subject, body) {
  try {
    console.log("Checking spam for subject:", subject.substring(0, 50) + "...");
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject, body })
    });

    const data = await response.json();

    if (data.error) {
      console.error("API returned error:", data.error);
      return { label: "ERROR", probability: 0 };
    }

    console.log("Spam check result:", data.label, data.probability);
    return { label: data.label, probability: data.probability };
  } catch (err) {
    console.error("API error:", err);
    return { label: "ERROR", probability: 0 };
  }
}

function injectResultBar(label, probability, bodyEl) {
  // Remove previous bar if exists
  const existingBar = document.getElementById("spam-result-bar");
  if (existingBar) existingBar.remove();

  // Create new bar
  const bar = document.createElement("div");
  bar.id = "spam-result-bar";
  bar.style.width = "100%";
  bar.style.padding = "10px";
  bar.style.color = "white";
  bar.style.fontWeight = "bold";
  bar.style.textAlign = "center";
  bar.style.borderRadius = "4px";
  bar.style.marginBottom = "10px";
  bar.style.fontFamily = "Arial, sans-serif";

  // Friendly message
  if (label === "SPAM") {
    bar.style.backgroundColor = "#ff4d4d";
    bar.innerText = `⚠️ This email is likely spam (${probability}%)`;
  } else if (label === "HAM") {
    bar.style.backgroundColor = "#4CAF50";
    bar.innerText = `✅ This email looks safe (${probability}%)`;
  } else {
    bar.style.backgroundColor = "#999";
    bar.innerText = `❓ Could not determine (${probability}%)`;
  }

  // Insert at the top of the email body
  bodyEl.prepend(bar);
  console.log("Injected result bar for label:", label);
}

// Run every 3 seconds, with a delay to handle async loading
setInterval(async () => {
  const email = getEmailContent();
  if (!email) return;

  const { subject, body, emailId, bodyEl } = email;

  // Skip if same email already processed
  if (emailId && emailId === lastEmailId) {
    console.log("Skipping - same email ID:", emailId);
    return;
  }
  lastEmailId = emailId;

  // Add a short delay to ensure content is fully loaded
  setTimeout(async () => {
    const result = await checkSpam(subject, body);
    injectResultBar(result.label, result.probability, bodyEl);
  }, 500); // 500ms delay
}, 3000);