import React, { useState, useEffect } from 'react';
import { Database, Search, Sparkles, Table2, Key, Link2, ArrowRight } from 'lucide-react';
import { fetchSchema, testRetrievalPlayground } from '../lib/api';

interface ColumnInfo {
  name: string;
  type: string;
  is_pk: boolean;
  comment?: string;
  sample_values?: any[];
}

interface ForeignKeyInfo {
  from_column: string;
  to_table: string;
  to_column: string;
  join_hint?: string;
}

interface TableSummary {
  name: string;
  schema: string;
  comment?: string;
  columns: ColumnInfo[];
  foreign_keys: ForeignKeyInfo[];
}

export const SchemaView: React.FC = () => {
  const [tables, setTables] = useState<TableSummary[]>([]);
  const [catalogHash, setCatalogHash] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTable, setSelectedTable] = useState<TableSummary | null>(null);
  const [loading, setLoading] = useState(true);

  // Playground state
  const [playgroundQuery, setPlaygroundQuery] = useState(
    'Find delinquent loans with high risk flag for customers in Mumbai'
  );
  const [playgroundResult, setPlaygroundResult] = useState<any>(null);
  const [isSearchingPlayground, setIsSearchingPlayground] = useState(false);

  useEffect(() => {
    fetchSchema()
      .then((data) => {
        setTables(data.tables || []);
        setCatalogHash(data.catalog_hash || '');
        if (data.tables && data.tables.length > 0) {
          setSelectedTable(data.tables[0]);
        }
      })
      .catch((err) => console.error('Failed to load schema:', err))
      .finally(() => setLoading(false));
  }, []);

  const handleTestPlayground = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playgroundQuery.trim() || isSearchingPlayground) return;
    setIsSearchingPlayground(true);
    try {
      const res = await testRetrievalPlayground(playgroundQuery);
      setPlaygroundResult(res);
    } catch (err) {
      console.error('Playground failed:', err);
    } finally {
      setIsSearchingPlayground(false);
    }
  };

  const filteredTables = tables.filter(
    (t) =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.schema.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.comment && t.comment.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-accent" />
            <h1 className="font-serif text-3xl sm:text-4xl text-ink font-normal">
              Schema Catalog & Semantic Memory
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-ink-2 font-sans mt-1">
            {tables.length} indexed relational tables with primary/foreign keys and business definitions.
          </p>
        </div>

        {catalogHash && (
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase tracking-wider text-ink-3 block">
              Deterministic Catalog Hash
            </span>
            <span className="font-mono text-xs text-ink font-semibold select-all">
              {catalogHash.slice(0, 16)}...
            </span>
          </div>
        )}
      </div>

      {/* Semantic Memory Retrieval Playground */}
      <div className="p-5 border-2 border-accent/20 rounded-xl bg-surface space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-accent" />
            <h3 className="font-serif text-xl text-ink">
              Semantic Memory Playground
            </h3>
          </div>
          <span className="text-xs font-mono text-ink-3">
            Top-k Vector Search + 1-Hop FK Expansion
          </span>
        </div>

        <form onSubmit={handleTestPlayground} className="flex gap-2">
          <input
            type="text"
            value={playgroundQuery}
            onChange={(e) => setPlaygroundQuery(e.target.value)}
            className="flex-1 px-3 py-2 text-xs bg-black/[0.02] dark:bg-white/[0.02] border border-line rounded-lg text-ink font-sans focus:outline-none focus:border-accent"
            placeholder="Type any natural language prompt to test slice retrieval..."
          />
          <button
            type="submit"
            disabled={isSearchingPlayground}
            className="px-4 py-2 bg-accent text-white rounded-lg text-xs font-mono font-medium hover:opacity-90 transition-all cursor-pointer disabled:opacity-50"
          >
            {isSearchingPlayground ? 'Indexing...' : 'Retrieve Slices'}
          </button>
        </form>

        {/* Playground Results */}
        {playgroundResult && (
          <div className="p-4 rounded-lg bg-black/[0.02] dark:bg-white/[0.02] border border-line space-y-3 font-mono text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <div className="p-2.5 rounded bg-surface border border-line">
                <span className="text-[10px] text-ink-3 uppercase block">Full Catalog Size</span>
                <span className="text-sm font-bold text-ink">
                  {playgroundResult.full_schema_chars.toLocaleString()} chars
                </span>
              </div>
              <div className="p-2.5 rounded bg-surface border border-line">
                <span className="text-[10px] text-ink-3 uppercase block">Retrieved Context</span>
                <span className="text-sm font-bold text-ink">
                  {playgroundResult.context_chars.toLocaleString()} chars
                </span>
              </div>
              <div className="p-2.5 rounded bg-surface border border-line col-span-2 sm:col-span-1">
                <span className="text-[10px] text-ink-3 uppercase block">Context Saved</span>
                <span className="text-sm font-bold text-ok">
                  {playgroundResult.context_saved_pct.toFixed(1)}% saved
                </span>
              </div>
            </div>

            {/* Retrieved Tables */}
            <div>
              <span className="text-[11px] uppercase tracking-wider text-ink-3 block mb-1">
                Relevant Table Slices ({playgroundResult.retrieved_tables.length}):
              </span>
              <div className="flex flex-wrap gap-1.5">
                {playgroundResult.retrieved_tables.map((tName: string) => (
                  <span
                    key={tName}
                    className="px-2 py-0.5 rounded text-[11px] bg-accent/10 text-accent font-bold border border-accent/20"
                  >
                    {tName}
                  </span>
                ))}
              </div>
            </div>

            {/* Matched Glossary Rules */}
            {playgroundResult.glossary_rules && playgroundResult.glossary_rules.length > 0 && (
              <div>
                <span className="text-[11px] uppercase tracking-wider text-ink-3 block mb-1">
                  Injected Business Glossary Rules:
                </span>
                <div className="p-2.5 rounded bg-surface border border-line text-xs font-sans text-ink space-y-1">
                  {playgroundResult.glossary_rules.map((rule: string, rIdx: number) => (
                    <div key={rIdx} className="flex items-start gap-1.5">
                      <span className="text-accent font-mono text-[10px] mt-0.5">•</span>
                      <span>{rule}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Two-Pane Catalog Browser */}
      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-ink-3">
          Loading schema catalog...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left: Searchable Table List */}
          <div className="space-y-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-ink-3 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter tables..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-surface border border-line rounded-lg text-ink font-mono focus:outline-none focus:border-accent"
              />
            </div>

            <div className="border border-line rounded-lg bg-surface max-h-[560px] overflow-y-auto divide-y divide-line">
              {filteredTables.map((t) => {
                const isSelected = selectedTable?.name === t.name;
                return (
                  <button
                    key={t.name}
                    type="button"
                    onClick={() => setSelectedTable(t)}
                    className={`w-full text-left p-2.5 flex items-center justify-between text-xs transition-colors cursor-pointer ${
                      isSelected
                        ? 'bg-accent/10 border-l-2 border-accent text-accent font-medium'
                        : 'hover:bg-black/5 dark:hover:bg-white/5 text-ink'
                    }`}
                  >
                    <div className="truncate">
                      <span className="text-[10px] font-mono text-ink-3 block">
                        {t.schema}
                      </span>
                      <span className="font-mono text-xs font-semibold">{t.name}</span>
                    </div>
                    <span className="text-[10px] font-mono text-ink-3">
                      {t.columns.length} cols
                    </span>
                  </button>
                );
              })}
              {filteredTables.length === 0 && (
                <div className="p-4 text-center text-xs text-ink-3 font-mono">
                  No matching tables found
                </div>
              )}
            </div>
          </div>

          {/* Right: Selected Table Details */}
          <div className="md:col-span-2 border border-line rounded-lg p-5 bg-surface space-y-5">
            {selectedTable ? (
              <>
                <div className="border-b border-line pb-3">
                  <div className="flex items-center gap-2">
                    <Table2 className="w-4 h-4 text-accent" />
                    <h2 className="font-mono text-lg font-bold text-ink">
                      {selectedTable.schema}.{selectedTable.name}
                    </h2>
                  </div>
                  {selectedTable.comment && (
                    <p className="text-xs text-ink-2 font-sans mt-1">
                      {selectedTable.comment}
                    </p>
                  )}
                </div>

                {/* Columns Table */}
                <div className="space-y-2">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-ink-3 font-medium">
                    Columns ({selectedTable.columns.length})
                  </div>
                  <div className="border border-line rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-black/[0.02] dark:bg-white/[0.02] border-b border-line">
                        <tr>
                          <th className="py-2 px-3 font-mono text-[10px] uppercase text-ink-3">
                            Name
                          </th>
                          <th className="py-2 px-3 font-mono text-[10px] uppercase text-ink-3">
                            Type
                          </th>
                          <th className="py-2 px-3 font-mono text-[10px] uppercase text-ink-3">
                            Key
                          </th>
                          <th className="py-2 px-3 font-mono text-[10px] uppercase text-ink-3">
                            Description
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-line font-mono text-xs">
                        {selectedTable.columns.map((c) => (
                          <tr
                            key={c.name}
                            className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02]"
                          >
                            <td className="py-2 px-3 font-semibold text-ink">{c.name}</td>
                            <td className="py-2 px-3 text-ink-3">{c.type}</td>
                            <td className="py-2 px-3">
                              {c.is_pk && (
                                <span className="inline-flex items-center gap-1 text-[10px] font-bold text-accent">
                                  <Key className="w-3 h-3" /> PK
                                </span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-ink-2 font-sans text-xs">
                              {c.comment || '-'}
                              {c.sample_values && c.sample_values.length > 0 && (
                                <div className="text-[10px] font-mono text-ink-3 mt-0.5">
                                  Examples: {c.sample_values.slice(0, 3).join(', ')}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Foreign Keys / Join Hints */}
                {selectedTable.foreign_keys && selectedTable.foreign_keys.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <div className="text-[11px] font-mono uppercase tracking-wider text-ink-3 font-medium flex items-center gap-1.5">
                      <Link2 className="w-3.5 h-3.5 text-accent" />
                      <span>Foreign Key Join Relationships</span>
                    </div>
                    <div className="divide-y divide-line border border-line rounded-lg font-mono text-xs">
                      {selectedTable.foreign_keys.map((fk, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 flex items-center justify-between text-ink"
                        >
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold">{fk.from_column}</span>
                            <ArrowRight className="w-3 h-3 text-ink-3" />
                            <span className="text-accent font-semibold">
                              {fk.to_table}.{fk.to_column}
                            </span>
                          </div>
                          {fk.join_hint && (
                            <span className="text-[10px] text-ink-3 bg-black/5 dark:bg-white/5 px-2 py-0.5 rounded">
                              {fk.join_hint}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="py-12 text-center text-xs font-mono text-ink-3">
                Select a table from the catalog to inspect schema and foreign keys.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
