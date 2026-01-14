import React, { useEffect, useState } from 'react';
import type { Novel } from '../types';
import { graphApi } from '../services/apiService';

interface GraphViewProps {
  novel: Novel;
}

const GraphView: React.FC<GraphViewProps> = ({ novel }) => {
  const [overview, setOverview] = useState<any>(null);
  const [consistency, setConsistency] = useState<any>(null);
  const [foreshadowings, setForeshadowings] = useState<any[]>([]);
  const [timelineChain, setTimelineChain] = useState<any[]>([]);
  const [worldSettings, setWorldSettings] = useState<any[]>([]);
  const [relations, setRelations] = useState<any[]>([]);
  const [causalCenterId, setCausalCenterId] = useState('');
  const [causalSummary, setCausalSummary] = useState('');
  const [causalChainItems, setCausalChainItems] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [relationSearchQuery, setRelationSearchQuery] = useState('');
  const [relationSearchResults, setRelationSearchResults] = useState<any[]>([]);
  const [relationSearchHops, setRelationSearchHops] = useState('2');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [relationSourceId, setRelationSourceId] = useState('');
  const [relationTargetId, setRelationTargetId] = useState('');
  const [relationType, setRelationType] = useState('');
  const [relationDescription, setRelationDescription] = useState('');
  const [relationWeight, setRelationWeight] = useState('');
  const [relationStage, setRelationStage] = useState('');
  const [relationFilterId, setRelationFilterId] = useState('');

  const loadGraphData = async () => {
    if (!novel?.id) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const [
        overviewData,
        consistencyData,
        foreshadowingData,
        chainData,
        worldData,
        relationData,
      ] = await Promise.all([
        graphApi.overview(novel.id),
        graphApi.consistencyCheck(novel.id),
        graphApi.foreshadowingStatus(novel.id),
        graphApi.causalChain(novel.id, undefined, 5),
        graphApi.worldSettings(novel.id),
        graphApi.characterRelations(novel.id),
      ]);
      setOverview(overviewData);
      setConsistency(consistencyData);
      setForeshadowings(foreshadowingData?.items || []);
      setTimelineChain(chainData?.items || []);
      setWorldSettings(worldData?.items || []);
      setRelations(relationData?.items || []);
    } catch (err: any) {
      setError(err?.message || 'Graph load failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (!novel?.id) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await graphApi.sync(novel.id);
      await loadGraphData();
    } catch (err: any) {
      setError(err?.message || 'Graph sync failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!novel?.id || !searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const result = await graphApi.search(novel.id, searchQuery.trim(), 30);
      setSearchResults(result?.items || []);
    } catch (err: any) {
      setError(err?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRelationSearch = async () => {
    if (!novel?.id || !relationSearchQuery.trim()) {
      setRelationSearchResults([]);
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const hops = Number(relationSearchHops) || 2;
      const result = await graphApi.searchRelations(novel.id, relationSearchQuery.trim(), hops, 40);
      setRelationSearchResults(result?.items || []);
    } catch (err: any) {
      setError(err?.message || 'Relation search failed');
    } finally {
      setLoading(false);
    }
  };

  const loadCausalSummary = async (centerId: string) => {
    if (!novel?.id || !centerId) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const result = await graphApi.causalSummary(novel.id, centerId, 3);
      setCausalSummary(result?.summary || '');
      setCausalChainItems(result?.items || []);
    } catch (err: any) {
      setError(err?.message || 'Causal summary failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRelation = async () => {
    if (!novel?.id) return;
    if (!relationSourceId || !relationTargetId || !relationType.trim()) {
      setError('Missing relation fields');
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await graphApi.createCharacterRelation(novel.id, {
        source_id: relationSourceId,
        target_id: relationTargetId,
        relation_type: relationType.trim(),
        description: relationDescription.trim(),
        weight: relationWeight ? Number(relationWeight) : undefined,
        stage: relationStage.trim() || undefined,
      });
      setRelationType('');
      setRelationDescription('');
      setRelationWeight('');
      setRelationStage('');
      await loadGraphData();
    } catch (err: any) {
      setError(err?.message || 'Create relation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRelations = async () => {
    if (!novel?.id) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await graphApi.generateCharacterRelations(novel.id);
      await loadGraphData();
    } catch (err: any) {
      setError(err?.message || 'Generate relations failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBackupRelations = async () => {
    if (!novel?.id) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const result = await graphApi.syncCharacterRelationsDb(novel.id);
      setNotice(`Backed up ${result?.upserted || 0} relations to database`);
    } catch (err: any) {
      setError(err?.message || 'Backup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExportRelations = async () => {
    if (!novel?.id) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const result = await graphApi.exportCharacterRelations(novel.id);
      const items = result?.items || [];
      const blob = new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${novel.title || 'novel'}-relations.json`;
      link.click();
      URL.revokeObjectURL(url);
      setNotice(`Exported ${items.length} relations`);
    } catch (err: any) {
      setError(err?.message || 'Export failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRelation = async (relationId: string) => {
    if (!novel?.id) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await graphApi.deleteCharacterRelation(novel.id, relationId);
      await loadGraphData();
    } catch (err: any) {
      setError(err?.message || 'Delete relation failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraphData();
  }, [novel?.id]);

  useEffect(() => {
    if (!causalCenterId && timelineChain.length > 0) {
      const firstId = timelineChain[0]?.id;
      if (firstId) {
        setCausalCenterId(firstId);
        loadCausalSummary(firstId);
      }
    }
  }, [timelineChain, causalCenterId]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Graph</h2>
          <p className="text-sm text-slate-500">Neo4j overview and checks</p>
        </div>
        <button
          onClick={handleSync}
          className="px-3 py-2 text-sm font-medium bg-slate-900 text-white rounded-md hover:bg-slate-800"
          disabled={loading}
        >
          Sync Graph
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{error}</div>
      )}
      {notice && (
        <div className="p-3 rounded-md bg-slate-50 text-slate-700 text-sm">{notice}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-white border border-slate-200">
          <div className="text-sm text-slate-500">Overview</div>
          <div className="mt-2 text-sm text-slate-700 space-y-1">
            <div>Volumes: {overview?.volumes ?? '-'}</div>
            <div>Chapters: {overview?.chapters ?? '-'}</div>
            <div>Characters: {overview?.characters ?? '-'}</div>
            <div>World Settings: {overview?.world_settings ?? '-'}</div>
            <div>Timeline Events: {overview?.timeline_events ?? '-'}</div>
            <div>Foreshadowings: {overview?.foreshadowings ?? '-'}</div>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-white border border-slate-200">
          <div className="text-sm text-slate-500">Consistency</div>
          <div className="mt-2 text-sm text-slate-700 space-y-1">
            <div>Timeline duplicate orders: {consistency?.timeline?.duplicate_orders?.length || 0}</div>
            <div>Timeline missing orders: {consistency?.timeline?.missing_orders?.length || 0}</div>
            <div>Timeline missing time: {consistency?.timeline?.missing_time?.length || 0}</div>
            <div>Foreshadowing issues: {consistency?.foreshadowings?.length || 0}</div>
            <div>Character age issues: {consistency?.characters?.length || 0}</div>
            <div>Location conflicts: {consistency?.locations?.length || 0}</div>
            <div>World rule conflicts: {consistency?.world_rules?.conflicts?.length || 0}</div>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-white border border-slate-200">
          <div className="text-sm text-slate-500">World Settings</div>
          <div className="mt-2 text-sm text-slate-700">
            {worldSettings.length === 0 ? (
              <div className="text-slate-400">No data</div>
            ) : (
              <ul className="list-disc ml-5 space-y-1">
                {worldSettings.slice(0, 6).map((w) => (
                  <li key={w.id}>{w.title}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg bg-white border border-slate-200">
          <div className="text-sm text-slate-500">Foreshadowing Status</div>
          <div className="mt-2 text-sm text-slate-700 space-y-2 max-h-64 overflow-auto">
            {foreshadowings.length === 0 ? (
              <div className="text-slate-400">No data</div>
            ) : (
              foreshadowings.slice(0, 20).map((f) => (
                <div key={f.id} className="border-b border-slate-100 pb-2">
                  <div className="font-medium">{f.content}</div>
                  <div className="text-xs text-slate-500">
                    intro: {f.intro_id || '-'} | resolved: {f.resolved_id || '-'} | status: {f.is_resolved}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="p-4 rounded-lg bg-white border border-slate-200">
          <div className="text-sm text-slate-500">Timeline Chain</div>
          <div className="mt-2 text-sm text-slate-700 space-y-2 max-h-64 overflow-auto">
            {timelineChain.length === 0 ? (
              <div className="text-slate-400">No data</div>
            ) : (
              timelineChain.map((t) => (
                <div key={t.id} className="border-b border-slate-100 pb-2">
                  <div className="font-medium">{t.event}</div>
                  <div className="text-xs text-slate-500">{t.time}</div>
                </div>
              ))
            )}
          </div>
          <div className="mt-3 space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <select
                value={causalCenterId}
                onChange={(e) => {
                  const nextId = e.target.value;
                  setCausalCenterId(nextId);
                  loadCausalSummary(nextId);
                }}
                className="px-2 py-1 border border-slate-300 rounded-md text-xs"
              >
                <option value="">Select event</option>
                {timelineChain.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.event}
                  </option>
                ))}
              </select>
              <button
                onClick={() => loadCausalSummary(causalCenterId)}
                className="px-2 py-1 text-xs border border-slate-300 rounded-md hover:bg-slate-50"
                disabled={loading || !causalCenterId}
              >
                Summarize
              </button>
            </div>
            {causalChainItems.length > 0 && (
              <div className="text-slate-500">
                {causalChainItems.map((item, index) => (
                  <span key={item.id}>
                    {item.event}
                    {index < causalChainItems.length - 1 ? ' → ' : ''}
                  </span>
                ))}
              </div>
            )}
            {causalSummary && (
              <div className="whitespace-pre-line text-slate-700">{causalSummary}</div>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 rounded-lg bg-white border border-slate-200">
        <div className="text-sm text-slate-500">World Rule Conflicts</div>
        <div className="mt-2 text-sm text-slate-700 space-y-2 max-h-64 overflow-auto">
          {consistency?.world_rules?.conflicts?.length ? (
            consistency.world_rules.conflicts.slice(0, 10).map((rule: any) => (
              <div key={rule.rule_id} className="border-b border-slate-100 pb-2">
                <div className="font-medium">{rule.title || 'Rule'}</div>
                {rule.description && (
                  <div className="text-xs text-slate-500">{rule.description}</div>
                )}
                <div className="text-xs text-slate-500 mt-1">
                  {rule.conflicts.slice(0, 5).map((conflict: any, idx: number) => (
                    <span key={`${rule.rule_id}-${conflict.event_id}-${idx}`}>
                      {conflict.phrase}: {conflict.event || conflict.event_id}
                      {idx < rule.conflicts.length - 1 ? ' · ' : ''}
                    </span>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="text-slate-400">No conflicts detected</div>
          )}
        </div>
      </div>

      <div className="p-4 rounded-lg bg-white border border-slate-200">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm text-slate-500">Character Relations</div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateRelations}
              className="px-3 py-1.5 text-xs font-medium border border-slate-300 rounded-md hover:bg-slate-50"
              disabled={loading}
            >
              Generate Relations
            </button>
            <button
              onClick={handleBackupRelations}
              className="px-3 py-1.5 text-xs font-medium border border-slate-300 rounded-md hover:bg-slate-50"
              disabled={loading}
            >
              Backup to DB
            </button>
            <button
              onClick={handleExportRelations}
              className="px-3 py-1.5 text-xs font-medium border border-slate-300 rounded-md hover:bg-slate-50"
              disabled={loading}
            >
              Export JSON
            </button>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-1 lg:grid-cols-5 gap-2">
          <select
            value={relationSourceId}
            onChange={(e) => setRelationSourceId(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
          >
            <option value="">Source</option>
            {novel.characters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            value={relationTargetId}
            onChange={(e) => setRelationTargetId(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
          >
            <option value="">Target</option>
            {novel.characters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            value={relationType}
            onChange={(e) => setRelationType(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
          >
            <option value="">Relation type</option>
            <option value="ally">ally</option>
            <option value="enemy">enemy</option>
            <option value="family">family</option>
            <option value="mentor">mentor</option>
            <option value="student">student</option>
            <option value="leader">leader</option>
            <option value="subordinate">subordinate</option>
            <option value="lover">lover</option>
            <option value="friend">friend</option>
            <option value="rival">rival</option>
          </select>
          <input
            value={relationWeight}
            onChange={(e) => setRelationWeight(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
            placeholder="Weight"
          />
          <button
            onClick={handleCreateRelation}
            className="px-3 py-2 text-sm font-medium bg-slate-900 text-white rounded-md hover:bg-slate-800"
            disabled={loading}
          >
            Add
          </button>
        </div>
        <div className="mt-2">
          <input
            value={relationDescription}
            onChange={(e) => setRelationDescription(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
            placeholder="Relation description (optional)"
          />
        </div>
        <div className="mt-2">
          <input
            value={relationStage}
            onChange={(e) => setRelationStage(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
            placeholder="阶段（例如 卷一/第3章）"
          />
        </div>
        <div className="mt-3 flex items-center gap-2 text-sm">
          <span className="text-slate-500">Filter:</span>
          <select
            value={relationFilterId}
            onChange={(e) => setRelationFilterId(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
          >
            <option value="">All</option>
            {novel.characters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="mt-3 text-sm text-slate-700 space-y-2 max-h-64 overflow-auto">
          {relations.length === 0 ? (
            <div className="text-slate-400">No relations</div>
          ) : (
            relations
              .filter((r) => {
                if (!relationFilterId) return true;
                return r.source_id === relationFilterId || r.target_id === relationFilterId;
              })
              .map((r) => (
                <div key={r.id} className="border-b border-slate-100 pb-2 flex items-center justify-between">
                  <div>
                    <div className="font-medium">
                      {r.source_name} → {r.target_name}
                    </div>
                    <div className="text-xs text-slate-500">{r.relation_type}</div>
                    {r.description && (
                      <div className="text-xs text-slate-500">{r.description}</div>
                    )}
                    {(r.weight || r.stage) && (
                      <div className="text-xs text-slate-500">
                        {r.weight ? `weight ${r.weight}` : ''}{r.weight && r.stage ? ' · ' : ''}{r.stage || ''}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteRelation(r.id)}
                    className="text-xs text-red-600 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
              ))
          )}
        </div>
      </div>

      <div className="p-4 rounded-lg bg-white border border-slate-200">
        <div className="text-sm text-slate-500">Graph Search</div>
        <div className="mt-2 flex gap-2">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-2 border border-slate-300 rounded-md text-sm"
            placeholder="Search characters, events, chapters..."
          />
          <button
            onClick={handleSearch}
            className="px-3 py-2 text-sm font-medium bg-slate-900 text-white rounded-md hover:bg-slate-800"
            disabled={loading}
          >
            Search
          </button>
        </div>
        <div className="mt-3 text-sm text-slate-700 space-y-1 max-h-56 overflow-auto">
          {searchResults.length === 0 ? (
            <div className="text-slate-400">No results</div>
          ) : (
            searchResults.map((item, idx) => (
              <div key={`${item.type}-${item.id}-${idx}`} className="border-b border-slate-100 pb-2">
                <div className="font-medium">{item.title}</div>
                <div className="text-xs text-slate-500">{item.type}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="p-4 rounded-lg bg-white border border-slate-200">
        <div className="text-sm text-slate-500">Relation Search</div>
        <div className="mt-2 flex flex-wrap gap-2">
          <input
            value={relationSearchQuery}
            onChange={(e) => setRelationSearchQuery(e.target.value)}
            className="flex-1 min-w-[200px] px-3 py-2 border border-slate-300 rounded-md text-sm"
            placeholder="Character name or role..."
          />
          <select
            value={relationSearchHops}
            onChange={(e) => setRelationSearchHops(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
          >
            <option value="1">1 hop</option>
            <option value="2">2 hops</option>
            <option value="3">3 hops</option>
          </select>
          <button
            onClick={handleRelationSearch}
            className="px-3 py-2 text-sm font-medium bg-slate-900 text-white rounded-md hover:bg-slate-800"
            disabled={loading}
          >
            Search
          </button>
        </div>
        <div className="mt-3 text-sm text-slate-700 space-y-1 max-h-56 overflow-auto">
          {relationSearchResults.length === 0 ? (
            <div className="text-slate-400">No results</div>
          ) : (
            relationSearchResults.map((item, idx) => (
              <div key={`${item.type}-${item.id}-${idx}`} className="border-b border-slate-100 pb-2">
                <div className="font-medium">{item.title}</div>
                <div className="text-xs text-slate-500">{item.type}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default GraphView;
