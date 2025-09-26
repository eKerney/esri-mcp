import { useState, useEffect } from 'react'
import { GoogleGenerativeAI } from '@google/generative-ai'
import './App.css'

interface Tool {
  name: string
  description: string
  inputSchema: any
}

interface MCPResponse {
  jsonrpc: string
  id: number
  result?: any
  error?: any
}

function App() {
  const [tools, setTools] = useState<Tool[]>([])
  const [query, setQuery] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [initialized, setInitialized] = useState(false)
  const [model, setModel] = useState<any>(null)

  useEffect(() => {
    initializeMCP()
    initializeGemini()
  }, [])

  const initializeGemini = async () => {
    const apiKey = import.meta.env.VITE_GOOGLE_API_KEY
    if (!apiKey) {
      console.error('VITE_GOOGLE_API_KEY not set')
      return
    }
    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`)
      const data = await response.json()
      console.log('Available Gemini models:', data.models?.map((m: any) => m.name) || 'None')
      const genAI = new GoogleGenerativeAI(apiKey)
       const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' })
      setModel(model)
    } catch (error) {
      console.error('Gemini init failed:', error)
    }
  }

  const sendMCPRequest = async (method: string, params: any = {}): Promise<any> => {
    const id = Date.now()
    const response = await fetch('/mcp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id,
        method,
        params
      })
    })

    if (!response.body) throw new Error('No response body')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.id === id) {
            return data
          }
        }
      }
    }
  }

  const initializeMCP = async () => {
    try {
      const response = await sendMCPRequest('initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'MCP Web Client', version: '1.0' }
      })
      console.log('Initialized:', response.result)
      setInitialized(true)
      await loadTools()
    } catch (error) {
      console.error('Initialize failed:', error)
      setResult('Failed to initialize MCP connection')
    }
  }

  const loadTools = async () => {
    try {
      const response = await sendMCPRequest('tools/list')
      setTools(response.result.tools)
    } catch (error) {
      console.error('Load tools failed:', error)
      setResult('Failed to load tools')
    }
  }

  const callTool = async (name: string, args: any) => {
    try {
      const response = await sendMCPRequest('tools/call', { name, arguments: args })
      return response.result
    } catch (error) {
      console.error('Tool call failed:', error)
      throw error
    }
  }

  const handleQuery = async () => {
    if (!query.trim() || !model) return
    setLoading(true)
    setResult('')

    try {
      // Prepare tools in Gemini format
      const geminiTools = [{
        functionDeclarations: tools.map(tool => ({
          name: tool.name,
          description: tool.description.split('\n')[0] + ' Available layers: states (use STATE_NAME = \'Michigan\'), counties (use STATEFP = \'26\'), usgs-gauges (use state = \'MI\'), rivers (use State = \'VA\'), dams, watersheds, impaired-waters, water-quality, sample-points.',
          parameters: tool.inputSchema
        }))
      }]

      const chat = model.startChat({
        tools: geminiTools
      })

      let result = await chat.sendMessage(query)
      let response = result.response
      console.log('Gemini response:', response)

      const functionCalls = response.functionCalls()
      if (functionCalls && functionCalls.length > 0) {
        const call = functionCalls[0]
        const toolName = call.name
        const args = call.args
        console.log('Calling tool:', toolName, 'with args:', args)

        // Call the tool
        const toolResult = await callTool(toolName, args)
        console.log('Tool result:', toolResult)

        // Send the tool result back to the model
        const functionResponse = {
          name: toolName,
          response: toolResult
        }

        result = await chat.sendMessage([{
          functionResponse
        }])

        response = result.response
        setResult(response.text() || JSON.stringify(toolResult, null, 2))
      } else {
        // No tool call
        setResult(response.text() || 'I can help you with geospatial data queries. Try asking about USGS gages, rivers, counties, or other geographic features.')
      }
    } catch (error) {
      console.error('Query failed:', error)
      setResult('Error processing query: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>MCP Esri Living Atlas Client</h1>
      {!initialized && <p>Initializing MCP connection...</p>}
      {initialized && model && (
        <>
          <div className="tools">
            <h2>Available Tools ({tools.length})</h2>
            <ul>
              {tools.map(tool => (
                <li key={tool.name}>
                  <strong>{tool.name}</strong>: {tool.description.split('\n')[0]}
                </li>
              ))}
            </ul>
          </div>
          <div className="query">
            <h2>Query</h2>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about geospatial data (e.g., 'How many USGS gages are in Michigan?')"
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
            />
            <button onClick={handleQuery} disabled={loading}>
              {loading ? 'Processing...' : 'Send Query'}
            </button>
          </div>
          {result && (
            <div className="result">
              <h2>Result</h2>
              <pre>{result}</pre>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default App
