"use client";

import { useState, useEffect, useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
} from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Trash2, 
  PlusCircle, 
  Search, 
  ShieldCheck, 
  User, 
  Globe, 
  Briefcase, 
  Lightbulb, 
  Eye, 
  EyeOff,
  MoreVertical,
  CheckCircle2,
  Clock,
  ArrowRight,
  Info,
  History,
  Zap,
  Target,
  FileText,
  MessageSquare,
  Calendar,
  Mail,
  ChevronRight,
  Sparkles,
  Brain,
  Lock,
  Bot
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { mockFactApi, Fact, FactVisibility, FactDomain, FactSuggestion } from '@/lib/mockFactsApi';
import { cn } from '@/lib/utils';

export default function PersonalFactsSettings() {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [suggestions, setSuggestions] = useState<FactSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | FactVisibility>('all');
  const [domainFilter, setDomainFilter] = useState<'all' | FactDomain>('all');
  const [showSensitive, setShowSensitive] = useState<Record<string, boolean>>({});
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const { toast } = useToast();

  // Form State
  const [newFactText, setNewFactText] = useState('');
  const [newVisibility, setNewVisibility] = useState<FactVisibility>('personal');
  const [newDomain, setNewDomain] = useState<FactDomain>('lifestyle');
  const [newCategory, setNewCategory] = useState('General');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [factsData, suggestionsData] = await Promise.all([
        mockFactApi.getFacts(),
        mockFactApi.getSuggestions()
      ]);
      setFacts(factsData);
      setSuggestions(suggestionsData);
    } catch (error) {
      toast({ title: "Error", description: "Failed to load knowledge vault.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const filteredFacts = useMemo(() => {
    return facts.filter(f => {
      const matchesSearch = f.text.toLowerCase().includes(searchQuery.toLowerCase()) || 
                           f.category.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesVisibility = activeTab === 'all' ? true : f.visibility === activeTab;
      const matchesDomain = domainFilter === 'all' ? true : f.domain === domainFilter;
      return matchesSearch && matchesVisibility && matchesDomain;
    });
  }, [facts, searchQuery, activeTab, domainFilter]);

  const stats = useMemo(() => {
    const maturity = Math.round((facts.reduce((acc, f) => acc + f.confidence, 0) / (facts.length || 1)) * 100);
    return {
      total: facts.length,
      private: facts.filter(f => f.visibility === 'private').length,
      maturity
    };
  }, [facts]);

  const handleAddFact = async () => {
    if (!newFactText.trim()) return;
    try {
      await mockFactApi.addFact({
        text: newFactText.trim(),
        visibility: newVisibility,
        domain: newDomain,
        category: newCategory,
        importance: 5,
        confidence: 1.0,
        source: 'Manual Entry',
        sourceType: 'manual'
      });
      setNewFactText('');
      setIsAddDialogOpen(false);
      loadData();
      toast({ title: "Memory Updated", description: "Karen has stored this fact in the neural vault." });
    } catch (e) {
      toast({ title: "Vault Failure", description: "Could not commit fact to long-term memory.", variant: "destructive" });
    }
  };

  const handleProcessSuggestion = async (id: string, status: 'accepted' | 'ignored') => {
    try {
      await mockFactApi.processSuggestion(id, status);
      loadData();
      toast({ 
        title: status === 'accepted' ? "Fact Confirmed" : "Suggestion Ignored", 
        description: status === 'accepted' ? "Insight has been promoted to permanent memory." : "Karen will ignore this insight pattern." 
      });
    } catch (e) {
      toast({ title: "Error", description: "Failed to process suggestion.", variant: "destructive" });
    }
  };

  const handleDeleteFact = async (id: string) => {
    try {
      await mockFactApi.deleteFact(id);
      loadData();
    } catch (e) {
      toast({ title: "Error", description: "Failed to delete fact.", variant: "destructive" });
    }
  };

  const getSourceIcon = (type: string | undefined) => {
    switch (type) {
      case 'gmail': return <Mail className="h-3 w-3" />;
      case 'calendar': return <Calendar className="h-3 w-3" />;
      case 'chat': return <MessageSquare className="h-3 w-3" />;
      case 'manual_sync': return <Zap className="h-3 w-3" />;
      default: return <FileText className="h-3 w-3" />;
    }
  };

  const getVisibilityIcon = (v: FactVisibility) => {
    switch(v) {
      case 'private': return <ShieldCheck className="h-3.5 w-3.5" />;
      case 'personal': return <User className="h-3.5 w-3.5" />;
      case 'global': return <Globe className="h-3.5 w-3.5" />;
    }
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Top Dashboard Widget - Pro Mockup Feature */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Neural Footprint', value: stats.total, sub: 'Verified across all domains', icon: Brain, color: 'text-indigo-400' },
          { label: 'Secure Enclaves', value: stats.private, sub: 'Items in restricted state', icon: Lock, color: 'text-rose-400' },
          { label: 'Knowledge Maturity', value: `${stats.maturity}%`, sub: 'Average confidence index', icon: Target, color: 'text-emerald-400' }
        ].map((stat, i) => (
          <div key={i} className="p-5 rounded-2xl border border-border/40 bg-card/30 backdrop-blur-sm flex items-center justify-between group hover:border-primary/20 transition-all">
            <div className="space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60">{stat.label}</p>
              <h4 className={cn("text-2xl font-black tracking-tighter", stat.color)}>{stat.value}</h4>
              <p className="text-[9px] font-medium text-muted-foreground/50 uppercase tracking-tight">{stat.sub}</p>
            </div>
            <div className="p-3 rounded-xl bg-background/50 border border-border/20 group-hover:bg-primary/5 transition-colors">
              <stat.icon className={cn("w-5 h-5", stat.color)} />
            </div>
          </div>
        ))}
      </div>

      <Separator className="bg-border/20" />

      {/* Main Fact Management Area */}
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1">
            <h3 className="text-xl font-bold tracking-tight">Memory Management</h3>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-widest opacity-60">Personal Profile &rsaquo; Facts</p>
          </div>
          <div className="flex items-center gap-3">
             <div className="relative group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-primary" />
                <Input 
                  placeholder="Query knowledge base..." 
                  className="pl-10 h-10 w-full sm:w-[280px] bg-background/40 border-border/40 rounded-xl text-xs uppercase font-bold tracking-tight"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
             </div>
             <Button onClick={() => setIsAddDialogOpen(true)} size="sm" className="rounded-xl h-10 px-5 font-bold uppercase tracking-widest text-[10px]">
                <PlusCircle className="mr-2 h-4 w-4" /> Add Memory
             </Button>
          </div>
        </div>

        <div className="flex items-center gap-4 py-2 border-y border-border/20">
           <div className="flex items-center gap-2">
              <span className="text-[9px] font-black uppercase text-muted-foreground/60 tracking-widest pl-2">Visibility:</span>
              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-auto">
                <TabsList className="bg-muted/40 h-8 p-1 rounded-lg border border-border/10">
                  <TabsTrigger value="all" className="h-6 px-3 text-[9px] font-bold uppercase">All</TabsTrigger>
                  <TabsTrigger value="personal" className="h-6 px-3 text-[9px] font-bold uppercase">Personal</TabsTrigger>
                  <TabsTrigger value="private" className="h-6 px-3 text-[9px] font-bold uppercase">Private</TabsTrigger>
                  <TabsTrigger value="global" className="h-6 px-3 text-[9px] font-bold uppercase">Global</TabsTrigger>
                </TabsList>
              </Tabs>
           </div>
           <Separator orientation="vertical" className="h-8" />
           <div className="flex items-center gap-2">
              <span className="text-[9px] font-black uppercase text-muted-foreground/60 tracking-widest">Domain:</span>
              <div className="flex gap-1.5">
                {['all', 'lifestyle', 'professional', 'business'].map((d) => (
                  <button 
                    key={d}
                    onClick={() => setDomainFilter(d as any)}
                    className={cn(
                      "px-3 py-1 rounded-lg text-[9px] font-black uppercase border transition-all",
                      domainFilter === d 
                        ? "bg-primary/10 border-primary/30 text-primary" 
                        : "bg-transparent border-border/20 text-muted-foreground/40 hover:text-foreground"
                    )}
                  >
                    {d}
                  </button>
                ))}
              </div>
           </div>
        </div>

        <ScrollArea className="h-[500px] w-full rounded-2xl">
          {loading ? (
             <div className="flex flex-col items-center justify-center h-[300px] opacity-30">
                <div className="w-10 h-10 rounded-full border-2 border-primary border-t-transparent animate-spin mb-4" />
                <span className="text-[10px] font-black uppercase tracking-widest">Accessing Neural Store...</span>
             </div>
          ) : filteredFacts.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 pr-4">
              {filteredFacts.map((fact) => (
                <div key={fact.id} className="group relative p-5 rounded-2xl border border-border/40 bg-card/20 hover:bg-card/40 transition-all duration-500 overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Brain className="w-12 h-12" />
                  </div>
                  
                  <div className="flex items-start justify-between relative z-10">
                    <div className="flex-1 space-y-4">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Badge variant="outline" className="text-[9px] font-black uppercase tracking-[0.1em] h-5 px-2 bg-background/50 border-border/30">
                          {getVisibilityIcon(fact.visibility)}
                          <span className="ml-1.5">{fact.visibility}</span>
                        </Badge>
                        <Badge variant="outline" className="text-[9px] font-black uppercase tracking-[0.1em] h-5 px-2 border-primary/20 text-primary/80">
                          {fact.domain}
                        </Badge>
                        <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-[0.25em]">{fact.category}</span>
                      </div>

                      <div className="relative">
                        {fact.visibility === 'private' && !showSensitive[fact.id] ? (
                          <div 
                            className="p-4 rounded-xl bg-orange-500/5 border border-orange-500/10 cursor-pointer flex items-center gap-3 transition-all hover:bg-orange-500/10"
                            onClick={() => setShowSensitive(p => ({...p, [fact.id]: true}))}
                          >
                            <Lock className="w-4 h-4 text-orange-500/60" />
                            <span className="text-[11px] font-bold text-muted-foreground/60 italic uppercase tracking-tighter">Sensitive record redacted. Resolve to view.</span>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <p className="text-base font-bold leading-relaxed tracking-tight text-foreground/90 max-w-2xl">
                              {fact.text}
                            </p>
                            <div className="flex items-center gap-6">
                               <div className="flex items-center gap-2">
                                  <div className="w-24 h-1 bg-zinc-900 rounded-full overflow-hidden">
                                     <div className="h-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" style={{ width: `${fact.confidence * 100}%` }} />
                                  </div>
                                  <span className="text-[9px] font-black text-indigo-400 uppercase">{Math.round(fact.confidence * 100)}% Match</span>
                               </div>
                               {fact.source && (
                                 <div className="flex items-center gap-1.5 text-[9px] font-bold text-zinc-500 uppercase tracking-tight hover:text-primary cursor-pointer transition-colors">
                                    {getSourceIcon(fact.sourceType)}
                                    <span>{fact.source}</span>
                                 </div>
                               )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                       <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full border border-transparent hover:border-border/40 hover:bg-muted/50 transition-all">
                               <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48 rounded-xl border-border/40 p-1">
                             <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest cursor-pointer rounded-lg">
                                <History className="mr-2 h-3.5 w-3.5" /> Use History
                             </DropdownMenuItem>
                             <DropdownMenuItem className="text-[10px] font-bold uppercase tracking-widest cursor-pointer rounded-lg text-rose-500 focus:text-rose-500" onClick={() => handleDeleteFact(fact.id)}>
                                <Trash2 className="mr-2 h-3.5 w-3.5" /> Purge Memory
                             </DropdownMenuItem>
                          </DropdownMenuContent>
                       </DropdownMenu>
                       <div className="mt-4 text-right">
                          <p className="text-[9px] font-black text-zinc-600 uppercase tracking-tighter">Usage Index</p>
                          <p className="text-xs font-black text-foreground/40">{fact.usage_count} hits</p>
                       </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 flex items-center justify-between border-t border-border/10 pt-3 opacity-40 group-hover:opacity-80 transition-opacity">
                     <span className="text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        First Detected: {new Date(fact.created_at).toLocaleDateString()}
                     </span>
                     {fact.last_used && (
                        <span className="text-[9px] font-black uppercase tracking-widest text-emerald-500 underline decoration-dotted">
                           Last context hit: {new Date(fact.last_used).toLocaleDateString()}
                        </span>
                     )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] border-2 border-dashed border-border/20 rounded-[2.5rem] bg-muted/5 opacity-40">
               <Sparkles className="w-10 h-10 mb-4 text-primary animate-pulse" />
               <h4 className="text-lg font-black uppercase tracking-tighter">Null Knowledge State</h4>
               <p className="text-[10px] uppercase font-bold tracking-widest text-center mt-1">Initialize the neural store by committing facts manually or through plugins.</p>
            </div>
          )}
        </ScrollArea>
      </div>

      <Separator className="bg-border/20" />

      {/* Suggested Insights - Premium Review Flow */}
      <div className="space-y-6">
         <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
               <div className="p-2 bg-amber-500/10 rounded-xl border border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.1)]">
                  <Lightbulb className="w-5 h-5 text-amber-500" />
               </div>
               <div>
                  <h3 className="text-lg font-black uppercase tracking-[0.1em]">Pending Neural Curation</h3>
                  <p className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-tight italic">AI extracted patterns awaiting user verification</p>
               </div>
            </div>
            <Badge variant="secondary" className="px-3 h-6 bg-amber-500/10 text-amber-500 font-black border-none animate-pulse">
               {suggestions.length} NEW INSIGHTS
            </Badge>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestions.map((sug) => (
               <div key={sug.id} className="p-6 rounded-[2rem] border bg-gradient-to-br from-indigo-500/[0.04] to-transparent border-primary/20 space-y-4 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                     <Target className="w-16 h-16 -rotate-45" />
                  </div>
                  
                  <div className="flex items-center justify-between pr-4">
                     <Badge className="bg-primary/10 text-primary border-none px-2 py-0 h-5 text-[9px] font-black tracking-widest">PATTERN DETECTED</Badge>
                     <span className="text-[9px] font-black uppercase tracking-widest text-indigo-400">Confidence: {Math.round(sug.confidence * 100)}%</span>
                  </div>
                  
                  <p className="text-base font-black leading-tight text-foreground/90">"{sug.text}"</p>
                  
                  <div className="p-4 rounded-xl bg-background/40 border border-white/5 space-y-2">
                     <div className="flex items-center gap-1.5 text-[9px] font-black uppercase text-zinc-500">
                        <Bot className="w-3 h-3" />
                        Karen's Reasoning
                     </div>
                     <p className="text-[10px] font-medium leading-relaxed text-muted-foreground/80 italic">
                        {sug.reasoning}
                     </p>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                     <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-600 uppercase">
                        {getSourceIcon('chat')}
                        {sug.source}
                     </div>
                     <div className="flex gap-2">
                        <Button 
                           size="sm" 
                           onClick={() => handleProcessSuggestion(sug.id, 'accepted')}
                           className="h-8 rounded-lg bg-primary text-[10px] font-black tracking-widest uppercase hover:px-8 transition-all"
                        >
                           TRUST & SAVE
                        </Button>
                        <Button 
                           size="sm" 
                           variant="ghost" 
                           onClick={() => handleProcessSuggestion(sug.id, 'ignored')}
                           className="h-8 rounded-lg text-[10px] font-black tracking-widest uppercase text-zinc-600 hover:text-rose-500"
                        >
                           IGNORE
                        </Button>
                     </div>
                  </div>
               </div>
            ))}
            {suggestions.length === 0 && (
               <div className="col-span-full p-8 rounded-[2rem] border border-dashed border-border/10 flex items-center justify-center bg-muted/5 opacity-50">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 italic">Continuous pattern monitoring active. No anomalies found.</p>
               </div>
            )}
         </div>
      </div>

      {/* Add Fact Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent className="sm:max-w-[500px] border-white/5 bg-[#0e0e0e] rounded-[2.5rem] p-10 overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.8)]">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500" />
          <DialogHeader className="mb-6">
            <DialogTitle className="text-2xl font-black uppercase tracking-tighter">Initialize Memory Frame</DialogTitle>
            <DialogDescription className="text-xs uppercase tracking-widest font-bold text-muted-foreground opacity-50">
              Commit verified knowledge to the long-term neural store
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="fact-text" className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 ml-1">Knowledge Content</Label>
              <div className="relative group">
                <FileText className="absolute left-4 top-4 w-4 h-4 text-zinc-700 group-focus-within:text-primary transition-colors" />
                <textarea 
                   id="fact-text" 
                   placeholder="e.g., Primary executive directive for Q2 is infrastructure scaling." 
                   className="w-full bg-black border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-sm font-bold placeholder:text-zinc-800 min-h-[100px] focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all resize-none"
                   value={newFactText}
                   onChange={(e) => setNewFactText(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 ml-1">Visibility Level</Label>
                <Select value={newVisibility} onValueChange={(v) => setNewVisibility(v as any)}>
                  <SelectTrigger className="h-12 bg-black border border-white/10 rounded-xl font-bold uppercase tracking-widest text-[10px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-black border-white/10 rounded-xl overflow-hidden shadow-2xl">
                    <SelectItem value="personal" className="flex items-center gap-2"><span className="text-[10px] font-black uppercase">Personal Profile</span></SelectItem>
                    <SelectItem value="private" className="flex items-center gap-2"><span className="text-[10px] font-black uppercase">Private Enclave</span></SelectItem>
                    <SelectItem value="global" className="flex items-center gap-2"><span className="text-[10px] font-black uppercase">Global Shared</span></SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 ml-1">Context Domain</Label>
                <Select value={newDomain} onValueChange={(v) => setNewDomain(v as any)}>
                  <SelectTrigger className="h-12 bg-black border border-white/10 rounded-xl font-bold uppercase tracking-widest text-[10px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-black border-white/10 rounded-xl overflow-hidden shadow-2xl">
                    <SelectItem value="lifestyle"><span className="text-[10px] font-black uppercase">Lifestyle Core</span></SelectItem>
                    <SelectItem value="professional"><span className="text-[10px] font-black uppercase">Professional Hub</span></SelectItem>
                    <SelectItem value="business"><span className="text-[10px] font-black uppercase">Business Matrix</span></SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 ml-1">Semantic Category</Label>
              <div className="relative group">
                 <Target className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-700" />
                 <Input 
                   placeholder="e.g., Working Style, Preference, Strategy" 
                   className="h-12 bg-black border border-white/10 rounded-xl pl-12 font-bold uppercase tracking-widest text-[10px]"
                   value={newCategory}
                   onChange={(e) => setNewCategory(e.target.value)}
                 />
              </div>
            </div>
          </div>

          <DialogFooter className="pt-10 flex flex-col sm:flex-row gap-3">
            <Button 
                type="button" 
                variant="ghost" 
                onClick={() => setIsAddDialogOpen(false)}
                className="flex-1 h-12 font-black uppercase tracking-[0.25em] text-[10px] text-zinc-500 hover:bg-white/5"
            >
                ABORT
            </Button>
            <Button 
              type="button" 
              onClick={handleAddFact}
              className="flex-1 h-12 bg-indigo-600 hover:bg-indigo-500 font-black uppercase tracking-[0.25em] text-[10px] shadow-[0_10px_30px_-5px_rgba(79,70,229,0.5)]"
              disabled={!newFactText.trim()}
            >
              INITIALIZE SYNC
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <style jsx global>{`
         @keyframes pulse-slow {
           0%, 100% { opacity: 1; filter: drop-shadow(0 0 5px rgba(99,102,241,0.5)); }
           50% { opacity: .7; filter: drop-shadow(0 0 2px rgba(99,102,241,0.2)); }
         }
         .animate-pulse-slow {
           animation: pulse-slow 3s infinite;
         }
      `}</style>
    </div>
  );
}