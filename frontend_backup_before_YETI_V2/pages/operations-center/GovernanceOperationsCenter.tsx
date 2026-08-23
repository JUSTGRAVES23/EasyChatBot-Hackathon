import GovernanceHero from "../../components/operations-center/GovernanceHero";
import GovernanceHealthScore from "../../components/operations-center/GovernanceHealthScore";
import GovernanceControlMatrix from "../../components/operations-center/GovernanceControlMatrix";
import GovernanceInsightCard from "../../components/operations-center/GovernanceInsightCard";
import GovernanceActivityTimeline from "../../components/operations-center/GovernanceActivityTimeline";
import "../../styles/operations-center.css";

export default function GovernanceOperationsCenter(){
 return <main className="governance-v3">
  <GovernanceHero/>
  <div className="governance-grid">
   <GovernanceHealthScore/>
   <GovernanceControlMatrix/>
  </div>
  <GovernanceInsightCard/>
  <GovernanceActivityTimeline/>
 </main>
}