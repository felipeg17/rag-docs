Feature: Create an interaction record
    As a rag-docs user,
    I want to ensure that the interaction creation in the persistent database works
    correctly.

    Scenario:
        Given the persistent database is running
        When a record of an interaction is created in the persistent database
        Then the interaction record should be retrievable from the persistent database