import { useState, useEffect } from 'react'
import { Container, Row, Col, Form, Button, Card, Spinner, Table, Alert } from 'react-bootstrap'
import 'bootstrap/dist/css/bootstrap.min.css'

interface Job {
  title: string
  company: string
  location: string
  url: string
  source: string
  score: number
  matching_keywords: string[]
}

function App() {
  const [query, setQuery] = useState('Junior Software Developer')
  const [location, setLocation] = useState('London, Ontario')
  const [password, setPassword] = useState('')
  const [runId, setRunId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<Job[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleHunt = async () => {
    if (!password) {
      setError('Please provide the access password.')
      return
    }

    setLoading(true)
    setError(null)
    const newRunId = `run_${Date.now()}`
    setRunId(newRunId)

    try {
      // Call our secure Vercel Proxy instead of GitHub directly
      const response = await fetch('/api/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          password: password,
          client_payload: {
            query,
            location,
            run_id: newRunId
          }
        })
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `Error: ${response.statusText}`)
      }

      console.log('Hunt triggered successfully!')
    } catch (err: any) {
      setError(err.message)
      setLoading(false)
    }
  }

  useEffect(() => {
    let interval: any
    if (loading && runId) {
      interval = setInterval(async () => {
        try {
          // Poll results from GitHub Pages
          const url = `https://n-oost.github.io/job-huntr/results/${runId}.json`
          const response = await fetch(url)
          if (response.ok) {
            const data = await response.json()
            setResults(data)
            setLoading(false)
            clearInterval(interval)
          }
        } catch (err) {
          console.log('Still waiting for results...')
        }
      }, 30000) // Poll every 30s
    }
    return () => clearInterval(interval)
  }, [loading, runId])

  return (
    <Container className="py-5">
      <Row className="justify-content-center mb-5">
        <Col md={8} className="text-center">
          <h1 className="display-4 mb-3">🛡️ JOB-HUNTR</h1>
          <p className="lead text-muted">Serverless Job Searching Powered by GitHub Actions</p>
        </Col>
      </Row>

      <Row className="justify-content-center mb-5">
        <Col md={6}>
          <Card className="shadow-sm">
            <Card.Body>
              <Form>
                <Form.Group className="mb-3">
                  <Form.Label>Job Title / Keywords</Form.Label>
                  <Form.Control 
                    type="text" 
                    value={query} 
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g. Junior Software Developer"
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Location</Form.Label>
                  <Form.Control 
                    type="text" 
                    value={location} 
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. London, Ontario"
                  />
                </Form.Group>

                <Form.Group className="mb-4">
                  <Form.Label>Access Password</Form.Label>
                  <Form.Control 
                    type="password" 
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter shared password..."
                  />
                  <Form.Text className="text-muted">
                    This secures the app from unauthorized use.
                  </Form.Text>
                </Form.Group>

                <div className="d-grid">
                  <Button 
                    variant="primary" 
                    size="lg" 
                    onClick={handleHunt}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        HUNTING...
                      </>
                    ) : 'START HUNT'}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {error && (
        <Row className="justify-content-center">
          <Col md={8}>
            <Alert variant="danger">{error}</Alert>
          </Col>
        </Row>
      )}

      {loading && (
        <Row className="justify-content-center mt-4">
          <Col md={8} className="text-center">
            <Spinner animation="grow" variant="primary" />
            <p className="mt-3 text-muted">The hunt has started! This usually takes 2-5 minutes. Please wait...</p>
          </Col>
        </Row>
      )}

      {results.length > 0 && (
        <Row className="mt-5">
          <Col>
            <h2 className="mb-4">🔥 Top Matches</h2>
            <Table striped bordered hover responsive className="shadow-sm">
              <thead className="table-dark">
                <tr>
                  <th>Score</th>
                  <th>Job Title</th>
                  <th>Company</th>
                  <th>Source</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {results.map((job, idx) => (
                  <tr key={idx}>
                    <td className="fw-bold text-primary">{job.score}</td>
                    <td>{job.title}</td>
                    <td>{job.company}</td>
                    <td><small className="text-muted">{job.source}</small></td>
                    <td>
                      <Button href={job.url} target="_blank" variant="outline-success" size="sm">
                        View & Apply
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Col>
        </Row>
      )}
    </Container>
  )
}

export default App
