<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />

</head>
<body>
<img src="https://github.com/user-attachments/assets/9456f70e-5971-436f-beb1-09e098498e7c">
<img src="https://github.com/user-attachments/assets/aa731f1a-854b-4f3e-a294-577f39ec5c68">

  <h1>StreamGuard AI</h1>

  <p><strong>Beta Version</strong></p>

  <h2>Overview</h2>
  <p>
    StreamGuard-AI is a Python-based tool designed to analyze live chat data from YouTube live streams to detect AI-like bots and estimate real viewer counts. This tool uses the YouTube Data API to monitor live chat messages, apply heuristics to detect bot-like behavior, and provides a user-friendly GUI for live updates.
  </p>

  <h2>Important Notice</h2>
  <ul>
    <li>The code is currently in <strong>beta</strong> stage and may contain bugs or incomplete features.</li>
    <li>The AI bot detection heuristics are experimental and in <strong>beta</strong>. Results should be interpreted with caution.</li>
  </ul>

  <h2>Features</h2>
  <ul>
    <li>Fetches live stream and chat data from specified YouTube channels.</li>
    <li>Analyzes chat messages to identify suspicious or bot-like accounts.</li>
    <li>Estimates real viewers vs bots in the live stream.</li>
    <li>Logs data for later review.</li>
    <li>Interactive GUI displaying channel info, viewer stats, and detection results.</li>
  </ul>

  <h2>Setup & Requirements</h2>
  <p>Make sure you have Python 3.x installed with the following packages:</p>
  <pre><code>google-api-python-client
Pillow
requests
</code></pre>
  <p>Also ensure you have a valid Google API key with YouTube Data API v3 enabled.</p>

  <h2>Usage</h2>
  <p>Run the script to start monitoring the specified YouTube channel's live stream. The GUI will update periodically with analysis results.</p>

  <h2>Contributing</h2>
  <p>Contributions, bug reports, and feature requests are welcome. Please open an issue or submit a pull request.</p>

  <h2>License</h2>
  <p>This project is licensed under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank" rel="noopener noreferrer">GNU General Public License v3.0</a>.</p>


</body>
</html>
