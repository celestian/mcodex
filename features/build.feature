Feature: build resolution

  Scenario: Build inside a text directory treats one arg as ref
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Story\" --author=celestian"
    And I cd into "text_story"
    When I run "mcodex snapshot draft-1 --note \"first\""
    And I run "mcodex build draft-1 --pipeline=noop"
    Then a file "{REPO_ROOT}/artifacts/story_draft-1.pdf" exists

  Scenario: Build from repo root treats one arg as text
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Story\" --author=celestian"
    When I run "mcodex build story --pipeline=noop"
    Then a file "artifacts/story_worktree.pdf" exists

  Scenario: Build outside repo requires a path
    Given an empty mcodex config
    When I run "mcodex author add celestian \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Story\" --author=celestian"
    And I cd to external directory "outside"
    Then running "mcodex build story --pipeline=noop" fails with "must be a path"
    When I run "mcodex build {REPO_ROOT}/text_story --pipeline=noop"
    Then a file "{REPO_ROOT}/artifacts/story_worktree.pdf" exists
