<div className="control-status">

    <h3>
        CONTROL STATUS
    </h3>


    <button
        className="control-row"
        onClick={() =>
            window.location.href =
            "/provider-management"
        }
    >

        <span>
            Provider Delivery
        </span>

        <strong>
            ✓ Healthy
        </strong>

    </button>



    <button
        className="control-row"
        onClick={() =>
            window.location.href =
            "/cybersecurity-center"
        }
    >

        <span>
            Cybersecurity
        </span>

        <strong>
            ✓ Monitoring
        </strong>

    </button>



    <button
        className="control-row"
        onClick={() =>
            window.location.href =
            "/operations-center/governance#audit"
        }
    >

        <span>
            Audit Evidence
        </span>

        <strong>
            ✓ Current
        </strong>

    </button>



    <button
        className="control-row"
        onClick={() =>
            window.location.href =
            "/operations-center/governance#timeline"
        }
    >

        <span>
            Changes
        </span>

        <strong>
            ✓ None
        </strong>

    </button>


</div>