import { useState, useEffect } from 'react'
import { CreateMLCEngine, MLCEngine } from '@mlc-ai/web-llm'
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
  const [engine, setEngine] = useState<MLCEngine | null>(null)
  const [modelLoading, setModelLoading] = useState(false)
  const [modelLoadProgress, setModelLoadProgress] = useState('')

  useEffect(() => {
    initializeMCP()
    loadModel()
  }, [])

  const loadModel = async () => {
    setModelLoading(true)
    setModelLoadProgress('Initializing WebLLM...')
    try {
      const engine = await CreateMLCEngine('Hermes-2-Pro-Mistral-7B-q4f16_1-MLC', {
        initProgressCallback: (progress) => {
          setModelLoadProgress(`Loading model: ${(progress.progress * 100).toFixed(1)}%`)
        }
      })
      setEngine(engine)
      setModelLoadProgress('Model loaded!')
    } catch (error) {
      console.error('Model load failed:', error)
      setModelLoadProgress('Failed to load model')
    } finally {
      setModelLoading(false)
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
    if (!query.trim() || !engine) return
    setLoading(true)
    setResult('')

    try {
      // Prepare tools in OpenAI format
      const openaiTools = tools.map(tool => ({
        type: 'function',
        function: {
          name: tool.name,
          description: tool.description.split('\n')[0],
          parameters: tool.inputSchema
        }
      }))

      const messages = [{ role: 'user', content: query }]
      const reply = await engine.chat.completions.create({
        messages,
        tools: openaiTools,
        tool_choice: 'auto'
      })

      const message = reply.choices[0].message
      console.log('LLM response:', message)

      if (message.tool_calls && message.tool_calls.length > 0) {
        const toolCall = message.tool_calls[0]
        const toolName = toolCall.function.name
        const args = JSON.parse(toolCall.function.arguments)
        console.log('Calling tool:', toolName, 'with args:', args)
        const toolResult = await callTool(toolName, args)
        setResult(JSON.stringify(toolResult, null, 2))
      } else {
        // No tool call
        setResult(message.content || 'I can help you with geospatial data queries. Try asking about USGS gages, rivers, counties, or other geographic features.')
        return
      }

      if (llmResponse.tool && llmResponse.args) {
        const toolResult = await callTool(llmResponse.tool, llmResponse.args)
        setResult(JSON.stringify(toolResult, null, 2))
      } else {
        setResult('No tool needed for this query, or unable to determine tool.')
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
      {modelLoading && <p>{modelLoadProgress}</p>}
      {initialized && engine && (
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
            <button onClick={handleQuery} disabled={loading || modelLoading}>
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
