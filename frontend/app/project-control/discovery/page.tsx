import { useCallback, useEffect, useState } from "react";
import { createProjectDiscoveryCandidate, listProjectDiscoveryCandidates, reviewProjectDiscoveryCandidate, acceptProjectDiscoveryCandidate, rejectProjectDiscoveryCandidate, type ProjectDiscoveryCandidate } from "@/app/lib/api/projectDiscovery";

export default function ProjectDiscoveryPage() {
  const [items,setItems]=useState<ProjectDiscoveryCandidate[]>([]);
  const [key,setKey]=useState(""); const [name,setName]=useState(""); const [source,setSource]=useState("internal");
  const [description,setDescription]=useState(""); const [owner,setOwner]=useState("");
  const [error,setError]=useState<string|null>(null); const [notice,setNotice]=useState<string|null>(null); const [busy,setBusy]=useState(false);
  const load=useCallback(async()=>{try{setItems(await listProjectDiscoveryCandidates());setError(null)}catch(e){setError(e instanceof Error?e.message:"Unable to load candidates.")}},[]);
  useEffect(()=>{void load()},[load]);
  async function create(e: React.FormEvent){e.preventDefault();setBusy(true);setError(null);try{
    const c=await createProjectDiscoveryCandidate({candidate_key:key.trim(),name:name.trim(),source:source.trim(),description:description.trim(),owner:owner.trim()||null});
    setItems(x=>[c,...x]);setKey("");setName("");setDescription("");setOwner("");setNotice("Discovery candidate created.");
  }catch(e){setError(e instanceof Error?e.message:"Unable to create candidate.")}finally{setBusy(false)}}
  async function action(c:ProjectDiscoveryCandidate, kind:"review"|"accept"|"reject"){setBusy(true);setError(null);try{
    const u=kind==="review"?await reviewProjectDiscoveryCandidate(c.candidate_id):kind==="accept"?await acceptProjectDiscoveryCandidate(c.candidate_id):await rejectProjectDiscoveryCandidate(c.candidate_id);
    setItems(x=>x.map(i=>i.candidate_id===u.candidate_id?u:i));setNotice(kind==="accept"?"Candidate registered through the Project Registry.":`Candidate ${kind}ed.`);
  }catch(e){setError(e instanceof Error?e.message:"Discovery operation failed.")}finally{setBusy(false)}}
  return <main style={{minHeight:"100vh",padding:"2rem",background:"var(--background,#0b1020)",color:"var(--foreground,#f5f7fb)"}}>
    <div style={{maxWidth:1100,margin:"0 auto"}}><header><p>PROJECT CONTROL CENTER</p><h1>Project Discovery</h1><p>Discover and review project candidates before authoritative registration.</p></header>
    {error&&<div role="alert">{error}</div>}{notice&&<div role="status">{notice}</div>}
    <section><h2>Create Discovery Candidate</h2><form onSubmit={create}>
      <input aria-label="Candidate key" placeholder="Candidate key" value={key} onChange={e=>setKey(e.target.value)} required/>
      <input aria-label="Name" placeholder="Project name" value={name} onChange={e=>setName(e.target.value)} required/>
      <input aria-label="Owner" placeholder="Owner" value={owner} onChange={e=>setOwner(e.target.value)}/>
      <input aria-label="Source" placeholder="Source" value={source} onChange={e=>setSource(e.target.value)} required/>
      <textarea aria-label="Description" placeholder="Description" value={description} onChange={e=>setDescription(e.target.value)}/>
      <button type="submit" disabled={busy}>Create Candidate</button></form></section>
    <section><h2>Discovery Candidates</h2><table><thead><tr><th>Project</th><th>Key</th><th>Source</th><th>Status</th><th>Actions</th></tr></thead><tbody>
      {items.map(c=><tr key={c.candidate_id}><td>{c.name}</td><td><code>{c.candidate_key}</code></td><td>{c.source}</td><td>{c.status}</td><td>
      {c.status==="discovered"&&<button onClick={()=>void action(c,"review")} disabled={busy}>Review</button>}
      {c.status==="reviewed"&&<><button onClick={()=>void action(c,"accept")} disabled={busy}>Accept & Register</button><button onClick={()=>void action(c,"reject")} disabled={busy}>Reject</button></>}</td></tr>)}
    </tbody></table></section></div></main>;
}
