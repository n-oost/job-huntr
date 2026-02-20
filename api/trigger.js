export default async function handler(request, response) {
  // 1. Only allow POST requests
  if (request.method !== 'POST') {
    return response.status(405).json({ error: 'Method not allowed' });
  }

  const { password, client_payload } = request.body;

  // 2. Validate Password (set this in Vercel Environment Variables)
  const CORRECT_PASSWORD = process.env.APP_PASSWORD;
  const GITHUB_TOKEN = process.env.GITHUB_PAT;
  const REPO_OWNER = process.env.GITHUB_USER || 'noahoosting';
  const REPO_NAME = 'job-huntr';

  if (!CORRECT_PASSWORD || !GITHUB_TOKEN) {
    return response.status(500).json({ error: 'Server misconfiguration: Secrets missing.' });
  }

  if (password !== CORRECT_PASSWORD) {
    return response.status(401).json({ error: 'Incorrect Password. Access Denied.' });
  }

  // 3. Trigger GitHub Action
  try {
    const ghResponse = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/dispatches`, {
      method: 'POST',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'JOB-HUNTR-Proxy'
      },
      body: JSON.stringify({
        event_type: 'hunt',
        client_payload: client_payload
      })
    });

    if (ghResponse.ok) {
      return response.status(200).json({ message: 'Hunt triggered successfully!' });
    } else {
      const errorText = await ghResponse.text();
      return response.status(ghResponse.status).json({ error: `GitHub API Error: ${errorText}` });
    }
  } catch (error) {
    return response.status(500).json({ error: error.message });
  }
}
