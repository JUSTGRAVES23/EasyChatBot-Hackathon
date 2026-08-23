from fastapi.testclient import TestClient

from run_backend import application


client = TestClient(application)


def test_decision_support_endpoint():


    response = client.post(

        "/api/cybersecurity-center/decision-brief",

        json={

            "signals":[

                {

                    "signal_id":
                    "demo-001",

                    "title":
                    "AI prompt injection attempt",

                    "severity":
                    "high",

                    "category":
                    "threat",

                    "confidence":
                    0.96,

                    "affected_area":
                    "AI layer",

                }

            ]

        }

    )


    assert response.status_code == 200


    body = response.json()


    assert (
        body["overall_priority"]
        ==
        "HIGH REVIEW REQUIRED"
    )