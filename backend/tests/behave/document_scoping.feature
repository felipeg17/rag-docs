Feature: DocumentScoping
    As a rag-docs user,
    I want retrieval on a document to be limited to that document,
    so that searching or asking about one document never returns chunks of another one.

    Background:
        Given the persistent database is running
        And the vector database is running
        And the backend is running
        And the pdf "ros-intro.pdf" is ingested with title "ros-intro"
        And the pdf "us-public-law-117-52.pdf" is ingested with title "us-public-law-117-52"

    Scenario: Search is scoped to the requested document
        When a search on "ros-intro" is made with "What does the Highway Trust Fund expenditure authority extension change to December 4, 2021?"
        Then every result belongs to the document "ros-intro"
        When a search on "ros-intro" is made with "What is ROS?"
        Then at least one result is returned
        And every result belongs to the document "ros-intro"

    Scenario: Standard ask is scoped to the requested document
        When a standard question is asked on "ros-intro" with "What does the Highway Trust Fund expenditure authority extension change to December 4, 2021?"
        Then every source document belongs to the document "ros-intro"
