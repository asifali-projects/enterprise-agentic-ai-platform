import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../lib/api';
import { Panel } from '../components/ui';

interface AgentCard {
  name?: string;
  description?: string;
  version?: string;
}
interface McpDiscovery {
  protocol?: string;
  version?: string;
}

export function Protocols() {
  const [card, setCard] = useState<AgentCard | null>(null);
  const [mcp, setMcp] = useState<McpDiscovery | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/a2a/.well-known/agent-card.json`)
      .then((response) => response.json())
      .then(setCard)
      .catch(() => setCard(null));
    fetch(`${API_BASE_URL}/api/v1/mcp/.well-known`)
      .then((response) => response.json())
      .then(setMcp)
      .catch(() => setMcp(null));
  }, []);

  return (
    <div className="page">
      <Panel eyebrow="Agent-to-Agent" title="A2A task contract">
        <p className="page__hint">{card?.description ?? 'Loading agent card…'}</p>
        <ul className="event-list">
          <li>
            <code>GET /api/v1/a2a/.well-known/agent-card.json</code> — capability discovery
          </li>
          <li>
            <code>POST /api/v1/a2a/tasks</code> — submit a task against a published workflow
          </li>
          <li>
            <code>GET /api/v1/a2a/tasks/&#123;task_id&#125;</code> — task status and result
          </li>
        </ul>
      </Panel>

      <Panel eyebrow="Model Context Protocol" title="Governed MCP gateway">
        <p className="page__hint">
          {mcp ? `${mcp.protocol} ${mcp.version} JSON-RPC gateway` : 'Loading MCP discovery…'}
        </p>
        <ul className="event-list">
          <li>
            <code>POST /api/v1/mcp</code> — JSON-RPC: <code>initialize</code>, <code>ping</code>,{' '}
            <code>tools/list</code>, <code>tools/call</code>
          </li>
          <li>
            <code>tools/call</code> requires a <code>project_id</code> and an <code>agent_id</code>;
            authorization is checked against the agent's tool permissions
          </li>
          <li>High-risk tools must run through an approval-backed workflow, never directly over MCP</li>
        </ul>
      </Panel>
    </div>
  );
}
