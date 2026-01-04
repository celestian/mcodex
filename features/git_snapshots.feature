Feature: git snapshots

  Scenario: Creating a snapshot creates a git tag
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Text\" --author=celestian"
    And I cd into "text_text"
    When I run "mcodex snapshot create draft --note \"first\""
    Then git tag "mcodex/text/draft-1" exists

  Scenario: Snapshot fails with a friendly message outside git
    Given an empty mcodex config
    And I remove git repository
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Text\" --author=celestian"
    And I cd into "text_text"
    Then running "mcodex snapshot create draft" fails with "Git repository not found"
