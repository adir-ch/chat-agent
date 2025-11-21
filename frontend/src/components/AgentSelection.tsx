import { useState, useEffect, FormEvent } from 'react';
import { getAgents } from '../services/api';
import type { AgentListItem } from '../types';

interface Props {
  onSelect: (agentId: string, agentName: string) => void;
}

export function AgentSelection({ onSelect }: Props) {
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAgents() {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getAgents();
        setAgents(data);
        if (data.length > 0) {
          setSelectedAgentId(data[0].agent_id);
        }
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : 'Failed to load agents');
      } finally {
        setIsLoading(false);
      }
    }

    fetchAgents();
  }, []);

  function formatAgentDisplay(agent: AgentListItem): string {
    const fullName = `${agent.first_name} ${agent.last_name}`;
    const areas = agent.areas.map((a) => a.name).join(', ');
    return `${fullName} | [${areas}] | Agency: ${agent.agency}`;
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (selectedAgentId) {
      const agent = agents.find((a) => a.agent_id === selectedAgentId);
      if (agent) {
        const agentName = `${agent.first_name} ${agent.last_name}`;
        onSelect(selectedAgentId, agentName);
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-zinc-500 animate-pulse">Loading agents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-zinc-500">No agents available</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="w-full max-w-3xl px-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="agent-select" className="block text-sm font-medium text-zinc-300 mb-2">
              Select an Agent
            </label>
            <select
              id="agent-select"
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-700 focus:border-transparent"
            >
              {agents.map((agent) => (
                <option key={agent.agent_id} value={agent.agent_id}>
                  {formatAgentDisplay(agent)}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={!selectedAgentId}
            className="w-full px-6 py-3 rounded-xl bg-accent text-zinc-950 font-medium disabled:opacity-60 disabled:cursor-not-allowed transition hover:opacity-90"
          >
            Submit
          </button>
        </form>
      </div>
    </div>
  );
}

