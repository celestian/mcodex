Feature: snapshots

  Scenario: Snapshot can be created from inside a text directory
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Článek o něčem\" --author=celestian"
    And I cd into "text_clanek_o_necem"
    When I run "mcodex snapshot draft-1 --note \"first\""
    Then snapshot "draft-1" exists
    And status shows current stage "draft"

  Scenario: Snapshot numbering increments within the same stage
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Text\" --author=celestian"
    And I cd into "text_text"
    When I run "mcodex snapshot draft-1"
    And I run "mcodex snapshot draft-2"
    Then snapshot "draft-2" exists

  Scenario: Snapshot label validation rejects invalid labels
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Text\" --author=celestian"
    And I cd into "text_text"
    Then running "mcodex snapshot bad/label" fails with "Invalid snapshot label"
