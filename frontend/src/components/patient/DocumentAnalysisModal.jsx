import React from 'react';
import {
  X,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Activity,
  Pill,
  FileText,
  Info,
  ShieldCheck,
  ExternalLink,
} from 'lucide-react';

export function DocumentAnalysisModal({
  isOpen,
  onClose,
  analysis,
  document,
  isLoading,
  error,
  onRetry,
}) {
  if (!isOpen) return null;

  const getConcernBadge = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'medium':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'low':
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        
        {/* Modal Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-indigo-900 via-indigo-800 to-sky-900 text-white flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/30 border border-indigo-400/40 flex items-center justify-center text-indigo-200">
              <Sparkles className="w-5 h-5 text-indigo-300 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white">AI Document Clinical Insight</h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/40 text-indigo-200 border border-indigo-400/30">
                  {analysis?.document_category || 'Clinical Analysis'}
                </span>
              </div>
              <p className="text-xs text-indigo-200/80">
                Document: <span className="font-medium text-white">{document?.title || 'Medical Record'}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-indigo-200 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-slate-50/50">
          
          {/* Loading State */}
          {isLoading && (
            <div className="py-16 text-center space-y-4">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 animate-spin">
                <Sparkles className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-semibold text-slate-800">Analyzing Document Text...</h4>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  Extracting medical records, parsing lab measurements, and identifying clinical observations responsibly.
                </p>
              </div>
            </div>
          )}

          {/* Error State */}
          {!isLoading && error && (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl space-y-3 text-center">
              <AlertTriangle className="w-8 h-8 text-rose-600 mx-auto" />
              <h4 className="text-sm font-bold text-rose-900">Analysis Unavailable</h4>
              <p className="text-sm text-rose-700 max-w-md mx-auto">{error}</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
                >
                  Retry Analysis
                </button>
              )}
            </div>
          )}

          {/* Analysis Content */}
          {!isLoading && !error && analysis && (
            <>
              {/* Mandatory Responsible AI Disclaimer */}
              <div className="p-4 bg-amber-50 border border-amber-200/80 rounded-xl flex items-start space-x-3">
                <ShieldCheck className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-amber-900 leading-relaxed">
                  <span className="font-bold">Informational Analysis Disclaimer: </span>
                  {analysis.disclaimer}
                </div>
              </div>

              {/* Summary Overview */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
                <div className="flex items-center space-x-2 text-indigo-950 font-bold text-sm">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <span>Executive Clinical Summary</span>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">
                  {analysis.summary}
                </p>
              </div>

              {/* Grid: Key Findings & Medications */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Key Findings */}
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <span>Identified Key Findings</span>
                  </div>
                  {analysis.key_findings && analysis.key_findings.length > 0 ? (
                    <ul className="space-y-2">
                      {analysis.key_findings.map((item, idx) => (
                        <li key={idx} className="flex items-start space-x-2 text-xs text-slate-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No specific discrete findings isolated.</p>
                  )}
                </div>

                {/* Detected Medications */}
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                    <Pill className="w-4 h-4 text-purple-600" />
                    <span>Referenced Medications</span>
                  </div>
                  {analysis.detected_medications && analysis.detected_medications.length > 0 ? (
                    <div className="space-y-2">
                      {analysis.detected_medications.map((med, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-purple-50/50 border border-purple-100 text-xs"
                        >
                          <span className="font-semibold text-purple-900">{med.name}</span>
                          <span className="text-purple-700 bg-purple-100/70 px-2 py-0.5 rounded font-mono text-[11px]">
                            {med.dosage || 'Standard'}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No prescription medications detected in visible text.</p>
                  )}
                </div>
              </div>

              {/* Detected Test Values & Clinical Measurements */}
              {analysis.detected_test_values && analysis.detected_test_values.length > 0 && (
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                    <Activity className="w-4 h-4 text-sky-600" />
                    <span>Extracted Lab Values & Measurements</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500">
                          <th className="py-2 px-3 font-semibold">Test / Parameter</th>
                          <th className="py-2 px-3 font-semibold">Recorded Value</th>
                          <th className="py-2 px-3 font-semibold">Reference Context</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {analysis.detected_test_values.map((val, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50">
                            <td className="py-2.5 px-3 font-semibold text-slate-900">{val.test}</td>
                            <td className="py-2.5 px-3 font-mono font-medium text-indigo-700">{val.value}</td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium border ${
                                  val.reference_context?.includes('Flagged') || val.reference_context?.includes('Higher') || val.reference_context?.includes('Lower')
                                    ? 'bg-amber-50 text-amber-800 border-amber-200'
                                    : 'bg-slate-100 text-slate-700 border-slate-200'
                                }`}
                              >
                                {val.reference_context || 'Recorded'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Potential Concerns / Observations */}
              {analysis.potential_concerns && analysis.potential_concerns.length > 0 && (
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Clinical Observations & Potential Discussions</span>
                  </div>
                  <div className="space-y-2">
                    {analysis.potential_concerns.map((concern, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border flex items-start space-x-3 text-xs ${getConcernBadge(
                          concern.level
                        )}`}
                      >
                        <span className="font-bold uppercase tracking-wider text-[10px] px-1.5 py-0.5 rounded bg-white/70 border border-current flex-shrink-0 mt-0.5">
                          {concern.level}
                        </span>
                        <span className="leading-relaxed">{concern.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Patient Friendly Explanation & Recommended Next Steps */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-sky-50/50 p-4 rounded-xl border border-sky-100 space-y-2">
                  <div className="flex items-center space-x-2 text-sky-900 font-bold text-xs">
                    <Info className="w-4 h-4 text-sky-600" />
                    <span>What This May Mean</span>
                  </div>
                  <p className="text-xs text-sky-800 leading-relaxed">
                    {analysis.patient_friendly_explanation}
                  </p>
                </div>

                <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100 space-y-2">
                  <div className="flex items-center space-x-2 text-indigo-900 font-bold text-xs">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <span>Recommended Next Step</span>
                  </div>
                  <p className="text-xs text-indigo-800 leading-relaxed">
                    {analysis.recommended_next_step}
                  </p>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-100 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
          <span className="text-[11px] text-slate-500 font-mono">
            Model: {analysis?.ai_model_name || 'CareAI-Clinical-Insight-v1'}
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            Close Analysis
          </button>
        </div>
      </div>
    </div>
  );
}

export default DocumentAnalysisModal;
