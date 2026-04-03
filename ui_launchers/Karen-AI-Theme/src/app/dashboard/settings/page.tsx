import React, { useState } from 'react';
import { 
  User, 
  Settings, 
  Cpu, 
  Save, 
  Shield, 
  Database, 
  Globe, 
  Bell, 
  Zap, 
  Clock,
  Search,
  Plus,
  MessageSquare,
  MoreVertical,
  Edit2,
  Trash2,
  ChevronRight,
  Lock,
  Wifi,
  Activity,
  HardDrive,
  Server,
  Microscope,
  Bot,
  Terminal,
  FileText,
  Brain,
  Info,
  AlertCircle,
  Settings2,
  Layers
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('assistant');
  const [activeSubTab, setActiveSubTab] = useState('general');

  const tabs = [
    { id: 'assistant', label: 'Assistant', icon: Bot },
    { id: 'personal', label: 'Personal', icon: User },
    { id: 'models', label: 'Models & Runtime', icon: Brain },
  ];

  const assistantSubTabs = [
    { id: 'general', label: 'General Behavior', icon: Bot },
    { id: 'memory', label: 'Memory Persistence', icon: Database },
    { id: 'governance', label: 'Governance & Truth', icon: Shield },
  ];

  const personalSubTabs = [
    { id: 'profile', label: 'User Profile', icon: User },
    { id: 'security', label: 'Security & Auth', icon: Lock },
    { id: 'preferences', label: 'Interface & Theme', icon: Settings },
  ];

  const modelsSubTabs = [
    { id: 'primary', label: 'Primary LLM', icon: Brain },
    { id: 'embedding', label: 'Embeddings', icon: Layers },
    { id: 'computation', label: 'Compute & GPU', icon: Cpu },
  ];

  const getSubTabs = () => {
    switch(activeTab) {
      case 'assistant': return assistantSubTabs;
      case 'personal': return personalSubTabs;
      case 'models': return modelsSubTabs;
      default: return [];
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-8 font-sans transition-all duration-500">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header Section */}
        <div className="flex flex-col space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-2xl border border-indigo-500/30 shadow-[0_0_20px_rgba(99,102,241,0.2)]">
              <Settings2 className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-4xl font-black bg-gradient-to-r from-white via-indigo-100 to-indigo-300 bg-clip-text text-transparent tracking-tighter uppercase">
                Application Settings
              </h1>
              <p className="text-indigo-300/40 font-medium tracking-wide flex items-center mt-1 uppercase text-[10px]">
                Configure your Karen AI experience with precision control
                <span className="ml-2 px-2 py-0.5 bg-indigo-500/10 rounded-full text-[8px] uppercase border border-indigo-500/20 tracking-tighter font-black">
                  Version 2.4.0
                </span>
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-10 items-start">
          {/* Main Navigation Sidebar */}
          <div className="space-y-6">
            <div className="bg-[#111111] rounded-[2rem] p-4 border border-white/5 shadow-2xl">
              <nav className="flex flex-col space-y-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id);
                      setActiveSubTab(getSubTabs().find(s => s.id === (activeSubTab)) ? activeSubTab : getSubTabs()[0]?.id || 'general');
                    }}
                    className={`group relative flex items-center space-x-4 p-4 rounded-2xl transition-all duration-300 ${ 
                      activeTab === tab.id 
                        ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-white border border-indigo-500/30' 
                        : 'text-zinc-500 hover:text-indigo-300 hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <div className={`p-2 rounded-xl transition-colors ${ 
                      activeTab === tab.id ? 'bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.4)]' : 'bg-zinc-800/50 group-hover:bg-zinc-700' 
                    }`}>
                      <tab.icon className={`w-5 h-5 ${activeTab === tab.id ? 'text-white' : 'text-zinc-400 font-bold group-hover:text-indigo-300'}`} />
                    </div>
                    <span className="font-black tracking-wider uppercase text-[11px]">{tab.label}</span>
                    {activeTab === tab.id && (
                      <motion.div 
                        layoutId="activeIndicator" 
                        className="absolute -right-2 w-1.5 h-8 bg-indigo-500 rounded-full shadow-[0_0_10px_rgba(99,102,241,1)]"
                      />
                    )}
                  </button>
                ))}
              </nav>
            </div>

            {/* Sub-menu styling - Refined for aesthetic */}
            <div className="bg-[#111111] rounded-[2rem] p-6 border border-white/5 shadow-2xl relative overflow-hidden group">
               {/* Background Glow */}
               <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 blur-[50px] opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
               
               <div className="flex items-center justify-between mb-6">
                 <span className="text-[10px] font-black uppercase text-zinc-500 tracking-[0.2em]">Configuration Nodes</span>
                 <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
               </div>
               
               <div className="flex flex-col space-y-2">
                 {getSubTabs().map((sub) => (
                   <button
                     key={sub.id}
                     onClick={() => setActiveSubTab(sub.id)}
                     className={`group flex items-center justify-between p-3 rounded-xl transition-all duration-300 ${ 
                       activeSubTab === sub.id 
                         ? 'text-white bg-indigo-500/10 font-black border border-indigo-500/20' 
                         : 'text-zinc-500 hover:text-zinc-200 hover:translate-x-1'
                     }`}
                   >
                     <div className="flex items-center space-x-3">
                       {sub.icon && <sub.icon className={`w-3.5 h-3.5 ${activeSubTab === sub.id ? 'text-indigo-400' : 'text-zinc-600'}`} />}
                       <span className="text-[10px] uppercase tracking-widest">{sub.label}</span>
                     </div>
                     <ChevronRight className={`w-3 h-3 transition-all duration-300 ${activeSubTab === sub.id ? 'rotate-90 text-indigo-400' : 'opacity-0 -translate-x-2'}`} />
                   </button>
                 ))}
               </div>
            </div>

            {/* System Health Widget */}
            <div className="bg-[#111111]/50 rounded-[2rem] p-6 border border-white/5">
               <div className="flex items-center justify-between mb-4">
                 <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">System Matrix</span>
                 <div className="flex items-center space-x-1">
                   <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-slow shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                   <span className="text-[9px] font-black text-emerald-500 uppercase tracking-tighter">Live Status</span>
                 </div>
               </div>
               
               <div className="space-y-4">
                 <div className="flex items-center justify-between">
                   <div className="flex items-center space-x-3">
                     <div className="p-1.5 bg-zinc-900 rounded-lg border border-white/5">
                       <HardDrive className="w-3 h-3 text-zinc-500" />
                     </div>
                     <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-tight">Active Context</span>
                   </div>
                   <span className="text-[10px] text-indigo-400 font-black tabular-nums">1.2 TB</span>
                 </div>
                 
                 <div className="w-full h-1 bg-zinc-900 rounded-full overflow-hidden border border-white/5">
                   <motion.div 
                     initial={{ width: 0 }}
                     animate={{ width: "64%" }}
                     className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                   />
                 </div>
                 
                 <div className="flex items-center justify-between">
                   <div className="flex items-center space-x-3">
                     <div className="p-1.5 bg-zinc-900 rounded-lg border border-white/5">
                       <Activity className="w-3 h-3 text-zinc-500" />
                     </div>
                     <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-tight">Token Velocity</span>
                   </div>
                   <span className="text-[10px] text-indigo-400 font-black tabular-nums">85 t/s</span>
                 </div>
               </div>
            </div>
          </div>

          {/* Main Content Area */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-[#111111] rounded-[2.5rem] border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.5)] min-h-[700px] overflow-hidden flex flex-col relative"
          >
            {/* Ambient Background Pattern */}
            <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-indigo-500/[0.03] to-transparent pointer-events-none" />

            {/* Active Section Header */}
            <div className="p-8 border-b border-white/5 bg-black/20 backdrop-blur-sm z-10">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2 text-indigo-400 mb-1">
                    <span className="text-[9px] font-black uppercase tracking-[0.25em]">{activeTab}</span>
                    <span className="text-zinc-800 text-xs">/</span>
                    <span className="text-[9px] font-black uppercase tracking-[0.25em] text-white">{activeSubTab}</span>
                  </div>
                  <h2 className="text-3xl font-black text-white tracking-tighter uppercase">
                    {getSubTabs().find(s => s.id === activeSubTab)?.label || 'Module Setup'}
                  </h2>
                </div>
                <button className="group flex items-center space-x-3 px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all duration-500 shadow-[0_0_30px_rgba(79,70,229,0.3)] hover:shadow-[0_0_40px_rgba(79,70,229,0.5)] hover:-translate-y-0.5 active:translate-y-0">
                  <Save className="w-4 h-4 transition-transform group-hover:scale-110" />
                  <span>Synchronize Config</span>
                </button>
              </div>
            </div>

            {/* Form Content Scroll Area */}
            <div className="flex-1 p-10 overflow-y-auto custom-scrollbar z-10">
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${activeTab}-${activeSubTab}`}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-12"
                >
                  {/* Dynamic sections based on tabs */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-zinc-600 tracking-[0.2em] ml-1">Entity Identification</label>
                      <div className="relative group">
                        <Bot className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 transition-colors group-focus-within:text-indigo-400" />
                        <input 
                          type="text" 
                          defaultValue="Karen Sovereign Intelligence"
                          className="w-full bg-black/40 border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-xs font-black uppercase tracking-tighter focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/30 transition-all placeholder:text-zinc-800"
                        />
                      </div>
                      <p className="text-[9px] text-zinc-600 font-bold uppercase tracking-tight ml-1 italic">Master identity for multi-channel propagation</p>
                    </div>
                    
                    <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-zinc-600 tracking-[0.2em] ml-1">Reasoning Threshold</label>
                      <div className="h-14 bg-black/40 border border-white/5 rounded-2xl px-6 flex items-center justify-between group hover:border-indigo-500/20 transition-all">
                        <div className="w-full flex items-center space-x-6">
                           <div className="flex-1 h-1.5 bg-zinc-900 rounded-full overflow-hidden border border-white/5">
                             <motion.div 
                               initial={{ width: 0 }}
                               animate={{ width: "85%" }}
                               className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
                           </div>
                           <span className="text-[10px] font-black text-indigo-400 w-10 text-right tabular-nums">0.85</span>
                        </div>
                      </div>
                      <p className="text-[9px] text-zinc-600 font-bold uppercase tracking-tight ml-1 italic">Probability floor for verified outputs</p>
                    </div>
                  </div>

                  <div className="p-8 rounded-[2.5rem] bg-gradient-to-br from-indigo-500/[0.07] to-purple-500/[0.07] border border-indigo-500/10 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
                       <Zap className="w-16 h-16 text-indigo-400" />
                    </div>
                    <div className="flex items-start space-x-6 relative z-10">
                      <div className="p-4 bg-indigo-500/10 rounded-[1.5rem] border border-indigo-500/20 shadow-xl">
                        <Cpu className="w-6 h-6 text-indigo-400" />
                      </div>
                      <div className="space-y-3">
                        <h4 className="text-[11px] font-black text-white uppercase tracking-[0.15em] text-indigo-100">Quantum Reasoning Core</h4>
                        <p className="text-[10px] text-zinc-500 font-medium leading-relaxed max-w-xl uppercase tracking-tighter">
                          Engage ultra-high-density computation clusters for parallel reasoning threads. 
                          Optimizes latent state management for sub-100ms latency across the neural fabric.
                        </p>
                        <div className="flex items-center space-x-8 mt-6">
                           <button className="flex items-center space-x-2 px-6 py-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all hover:bg-indigo-500/20 hover:scale-105 active:scale-95">
                             <Terminal className="w-3.5 h-3.5" />
                             <span>Ignition Test</span>
                           </button>
                           <div className="flex items-center space-x-4">
                              <div className="w-12 h-6 bg-indigo-500/20 rounded-full relative p-1 cursor-pointer group/toggle border border-indigo-500/30">
                                <div className="absolute left-1 top-1 w-4 h-4 bg-indigo-400 rounded-full transition-all group-hover:scale-110 shadow-[0_0_10px_rgba(99,102,241,1)] translate-x-6" />
                              </div>
                              <span className="text-[9px] font-black text-zinc-300 uppercase tracking-tighter">Optimized Overdrive</span>
                           </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[ 
                      { label: 'Neural Buffer', icon: Brain, value: 'Tier 5' }, 
                      { label: 'Entropy Sink', icon: Microscope, value: 'Active' }, 
                      { label: 'Governed Link', icon: Shield, value: 'Encrypted' } 
                    ].map((item, idx) => (
                      <div key={idx} className="p-6 rounded-[2rem] bg-zinc-900/40 border border-white/5 hover:border-indigo-500/20 transition-all group hover:bg-black/60 cursor-crosshair">
                         <item.icon className="w-6 h-6 text-zinc-700 mb-4 group-hover:text-indigo-400 transition-all duration-500 group-hover:rotate-12" />
                         <div className="text-[9px] font-black text-zinc-600 uppercase tracking-[0.2em] mb-1">{item.label}</div>
                         <div className="text-xs font-black text-white uppercase tracking-widest">{item.value}</div>
                      </div>
                    ))}
                  </div>

                  <div className="space-y-6">
                    <div className="flex items-center justify-between px-1">
                       <h4 className="text-[10px] font-black uppercase text-zinc-600 tracking-[0.25em]">Critical Manifest Config</h4>
                       <button className="p-2 bg-zinc-900 rounded-xl border border-white/10 hover:border-indigo-500/40 transition-all">
                          <Plus className="w-4 h-4 text-indigo-400" />
                       </button>
                    </div>
                    <div className="space-y-3">
                      {[
                        { key: 'sovereign_governance', val: 'active', type: 'Level 5' },
                        { key: 'memory_retention_ms', val: '24,000', type: 'Temporal' },
                        { key: 'adversarial_filter', val: 'strict', type: 'Defense' }
                      ].map((tag, idx) => (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          key={idx} 
                          className="flex items-center justify-between p-5 bg-white/[0.01] border border-white/5 rounded-2xl group hover:bg-indigo-500/[0.02] hover:border-indigo-500/20 transition-all"
                        >
                           <div className="flex items-center space-x-6">
                             <span className="text-[11px] font-mono text-indigo-300/60 uppercase tracking-tighter">{tag.key}</span>
                             <div className="px-2 py-0.5 bg-zinc-800 rounded-md text-[8px] font-black uppercase text-zinc-500 border border-white/5">{tag.type}</div>
                           </div>
                           <div className="flex items-center space-x-6">
                             <span className="text-[11px] font-black text-white uppercase tracking-widest tabular-nums">{tag.val}</span>
                             <MoreVertical className="w-4 h-4 text-zinc-800 cursor-pointer hover:text-white transition-colors" />
                           </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>

      <style jsx global>{`
        .animate-pulse-slow {
          animation: pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: .5; }
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #222;
          border-radius: 10px;
          border: 2px solid #000;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #333;
        }
      `}</style>
    </div>
  );
}
