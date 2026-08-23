export default function GovernanceActivityTimeline({events=[]}:any){
 return <section className="governance-card">
  <small>GOVERNANCE ACTIVITY</small>
  <h2>Timeline</h2>
  {events.length===0 ? <p>No governance events detected.</p> :
   events.map((e:any)=><p key={e.timestamp}>{e.event}</p>)}
 </section>
}