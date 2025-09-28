export interface Tool {
  name: string
  description: string
  inputSchema: any
}

export interface MCPResponse {
  jsonrpc: string
  id: number
  result?: any
  error?: any
}

export class MCPClient {
  private baseUrl: string

  constructor(baseUrl: string = '/mcp') {
    this.baseUrl = baseUrl
  }

  async sendRequest(method: string, params: any = {}): Promise<any> {
    const id = Date.now()
    const response = await fetch(this.baseUrl, {
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

  async initialize(): Promise<any> {
    return this.sendRequest('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'MCP Web Client', version: '1.0' }
    })
  }

  async listTools(): Promise<Tool[]> {
    const response = await this.sendRequest('tools/list')
    return response.result.tools
  }

  async callTool(name: string, args: any): Promise<any> {
    const response = await this.sendRequest('tools/call', { name, arguments: args })
    return response.result
  }
}