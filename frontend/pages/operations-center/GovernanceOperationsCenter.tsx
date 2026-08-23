import { useNavigate } from "react-router-dom";

import "../../styles/operations-center.css";


export default function GovernanceOperationsCenter() {


    const navigate = useNavigate();



    return (

        <div className="governance-v3">


            {/* =====================================================
                HERO
            ====================================================== */}

            <section className="governance-hero">


                <div>


                    <small>
                        EASYCHATBOT OPERATIONS CENTER
                    </small>



                    <h1>
                        AI Governance Center
                    </h1>



                    <p>
                        Governance visibility, operational controls and audit
                        evidence remain under authorised human control.
                    </p>



                    <span className="status-pill">
                        ● Governance operating normally
                    </span>


                </div>



                <div className="yeti-hero">


                    <img
                        src="/assets/characters/yeti-governance.png"
                        alt="YETI Governance Guardian"
                    />


                </div>


            </section>





            {/* =====================================================
                HEALTH + CONTROL STATUS
            ====================================================== */}


            <section className="governance-grid">



                <div className="governance-card">


                    <small>
                        GOVERNANCE HEALTH
                    </small>



                    <div className="health-value">
                        96%
                    </div>



                    <div className="health-bar">

                        <span />

                    </div>



                    <p>
                        All governance controls are operating normally.
                    </p>


                </div>





                <div className="governance-card">


                    <small>
                        CONTROL STATUS
                    </small>



                    <div className="control-list">



                        {/* PROVIDER MANAGEMENT */}

                        <button

                            type="button"

                            className="control-row"

                            onClick={() =>
                                navigate(
                                    "/operations-center/providers"
                                )
                            }

                        >

                            <span>
                                Provider Delivery
                            </span>


                            <strong>
                                ✓ Healthy
                            </strong>


                        </button>





                        {/* CYBERSECURITY */}

                        <button

                            type="button"

                            className="control-row"

                            onClick={() =>
                                navigate(
                                    "/operations-center/cybersecurity"
                                )
                            }

                        >

                            <span>
                                Cybersecurity
                            </span>


                            <strong>
                                ✓ Monitoring
                            </strong>


                        </button>






                        {/* GOVERNANCE */}

                        <button

                            type="button"

                            className="control-row"

                            onClick={() =>
                                navigate(
                                    "/operations-center/governance"
                                )
                            }

                        >

                            <span>
                                Audit Evidence
                            </span>


                            <strong>
                                ✓ Current
                            </strong>


                        </button>






                        {/* STATIC STATUS */}

                        <button

                            type="button"

                            className="control-row"

                        >

                            <span>
                                Changes
                            </span>


                            <strong>
                                ✓ None
                            </strong>


                        </button>




                    </div>


                </div>


            </section>








            {/* =====================================================
                YETI INSIGHT
            ====================================================== */}



            <section className="governance-card yeti-insight">


                <small>
                    YETI GOVERNANCE INSIGHT
                </small>



                <h2>
                    Everything looks calm from a governance perspective.
                </h2>



                <p>

                    YETI explains governance state and evidence.
                    Human operators remain responsible for decisions.

                </p>



            </section>








            {/* =====================================================
                TIMELINE
            ====================================================== */}



            <section className="governance-card">


                <small>
                    GOVERNANCE ACTIVITY
                </small>



                <h2>
                    Timeline
                </h2>



                <div className="timeline-empty">

                    No governance events detected.

                </div>



            </section>



        </div>


    );

}