import { useState, useEffect } from 'react'
import { GoogleGenerativeAI } from '@google/generative-ai'
import { MCPClient, type Tool } from './mcpClient'
import './App.css'

function App() {
  const [tools, setTools] = useState<Tool[]>([])
  const [query, setQuery] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [initialized, setInitialized] = useState(false)
  const [model, setModel] = useState<any>(null)
  const [client, setClient] = useState<MCPClient | null>(null)

  const prettyNames: { [key: string]: string } = {
    'query_geojson': 'Get GeoJSON Data',
    'query_layer': 'Query Layer',
    'query_point_layer': 'Query Point Layer',
    'get_layer_fields': 'Get Layer Fields',
    'get_state_geometry': 'Get State Geometry',
    'save_geojson': 'Save GeoJSON',
    'display_geojson': 'Display GeoJSON',
    'create_arcgis_app': 'Create ArcGIS App',
    'create_arcgis_app_with_rivers': 'Create ArcGIS App with Rivers',
    'create_water_map_context': 'Create Water Map Context',
    'create_embeddable_water_map': 'Create Embeddable Water Map'
  }

  useEffect(() => {
    const mcpClient = new MCPClient()
    setClient(mcpClient)
    initializeMCP(mcpClient)
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

  const initializeMCP = async (mcpClient: MCPClient) => {
    try {
      const response = await mcpClient.initialize()
      console.log('Initialized:', response.result)
      setInitialized(true)
      await loadTools(mcpClient)
    } catch (error) {
      console.error('Initialize failed:', error)
      setResult('Failed to initialize MCP connection')
    }
  }

  const loadTools = async (mcpClient: MCPClient) => {
    try {
      const tools = await mcpClient.listTools()
      setTools(tools)
    } catch (error) {
      console.error('Load tools failed:', error)
      setResult('Failed to load tools')
    }
  }

  const callTool = async (name: string, args: any) => {
    if (!client) throw new Error('MCP client not initialized')
    try {
      return await client.callTool(name, args)
    } catch (error) {
      console.error('Tool call failed:', error)
      throw error
    }
  }

  const handleQuery = async () => {
    if (!query.trim() || !model || !client) return
    setLoading(true)
    setResult('')

    try {
      // Prepare tools in Gemini format
      const geminiTools = [{
        functionDeclarations: tools.map(tool => ({
          name: tool.name,
          description: tool.description,
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
        setResult(response.text() || toolResult)
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
      {initialized && model && client && (
        <>
          <div className="tools">
            <h2>Available Tools ({tools.length})</h2>
            <ul>
              {tools.map(tool => (
                <li key={tool.name}>
                  <strong>{prettyNames[tool.name] || tool.name}</strong>: {tool.description.split('\n')[0]}
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
               {result && typeof result === 'string' && result.includes('<!DOCTYPE html>') ? (
                <>
                  <div style={{ marginBottom: '10px' }}>
                    <button onClick={() => {
                      const html = result.substring(result.indexOf('<!DOCTYPE html>'));
                      const blob = new Blob([html], { type: 'text/html' });
                      const url = URL.createObjectURL(blob);
                      window.open(url);
                    }}>
                      Open Map in New Tab
                    </button>
                  </div>
                  <iframe srcDoc={result.substring(result.indexOf('<!DOCTYPE html>'))} style={{ width: '100%', height: '600px', border: '1px solid #ccc' }} />
                  <details>
                    <summary>View HTML Source</summary>
                    <pre>{result}</pre>
                  </details>
                </>
              ) : (
                <pre>{result}</pre>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default App
