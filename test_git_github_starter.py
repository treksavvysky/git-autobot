import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import os
import json
import sys

# Add the directory containing git_github_starter to sys.path
# This is often needed if the test file is not in the same directory as the module
# For this environment, assuming they are accessible or this path adjustment helps.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Functions and classes to test from git_github_starter
# We need to be careful with imports if functions use other functions from the same module
# that we might want to mock separately.
import git_github_starter as ggs

# Mock constants from the ggs module that are used by functions
ggs.REPO_CONFIG_FILE = 'test_repo_config.json'

class TestConfigManagement(unittest.TestCase):

    def setUp(self):
        # Ensure a clean slate for each test involving the config file
        if os.path.exists(ggs.REPO_CONFIG_FILE):
            os.remove(ggs.REPO_CONFIG_FILE)

    def tearDown(self):
        # Clean up the dummy config file after tests
        if os.path.exists(ggs.REPO_CONFIG_FILE):
            os.remove(ggs.REPO_CONFIG_FILE)

    def test_load_repo_config_no_file(self):
        """Test loading config when the file does not exist."""
        self.assertEqual(ggs.load_repo_config(), {})

    def test_save_and_load_repo_config(self):
        """Test saving a config and then loading it."""
        test_config = {"repo1": "/path/to/repo1", "repo2": "/path/to/repo2"}
        ggs.save_repo_config(test_config)
        loaded_config = ggs.load_repo_config()
        self.assertEqual(loaded_config, test_config)

    def test_load_repo_config_io_error(self):
        """Test loading config with an IOError during open."""
        with patch('builtins.open', mock_open()) as mocked_open:
            mocked_open.side_effect = IOError("File access error")
            # Need to ensure os.path.exists returns True for the error path to be triggered in load_repo_config
            with patch('os.path.exists', return_value=True):
                config = ggs.load_repo_config()
                self.assertEqual(config, {})

    def test_load_repo_config_json_decode_error(self):
        """Test loading config with a JSONDecodeError."""
        with patch('builtins.open', mock_open(read_data="invalid json")) as mocked_open:
             with patch('os.path.exists', return_value=True):
                config = ggs.load_repo_config()
                self.assertEqual(config, {})

    def test_save_repo_config_io_error(self):
        """Test saving config with an IOError."""
        test_config = {"repo1": "/path/to/repo1"}
        with patch('builtins.open', mock_open()) as mocked_open:
            mocked_open.side_effect = IOError("File access error")
            # Suppress print output during test
            with patch('builtins.print') as mock_print:
                ggs.save_repo_config(test_config)
                # Check if the error message was printed (optional)
                # mock_print.assert_any_call(f"Error saving repository configuration: File access error")
        # Ensure file was not created or is empty if error occurred (harder to check without knowing mock_open behavior on error)
        self.assertFalse(os.path.exists(ggs.REPO_CONFIG_FILE))


    def test_add_repo_to_config(self):
        """Test adding a new repository to the config."""
        ggs.add_repo_to_config("new_repo", "/path/to/new_repo")
        loaded_config = ggs.load_repo_config()
        self.assertIn("new_repo", loaded_config)
        self.assertEqual(loaded_config["new_repo"], "/path/to/new_repo")

        # Test updating an existing repository
        ggs.add_repo_to_config("new_repo", "/updated/path/to/new_repo")
        loaded_config_updated = ggs.load_repo_config()
        self.assertEqual(loaded_config_updated["new_repo"], "/updated/path/to/new_repo")

    def test_get_repo_path_from_config(self):
        """Test retrieving a repository path from the config."""
        ggs.add_repo_to_config("repo_A", "/path/A")
        self.assertEqual(ggs.get_repo_path_from_config("repo_A"), "/path/A")
        self.assertIsNone(ggs.get_repo_path_from_config("non_existent_repo"))

    @patch('builtins.print') # Suppress print output
    def test_list_repos_from_config_empty(self, mock_print):
        """Test listing repositories when config is empty."""
        ggs.list_repos_from_config()
        mock_print.assert_any_call("No repositories found in the configuration.")

    @patch('builtins.print') # Suppress print output
    def test_list_repos_from_config_with_data(self, mock_print):
        """Test listing repositories when config has data."""
        ggs.add_repo_to_config("repoX", "/path/X")
        ggs.add_repo_to_config("repoY", "/path/Y")
        ggs.list_repos_from_config()

        # Check if the items were printed. Order might vary with dicts in older Python,
        # but for simple checks, any_call is fine.
        mock_print.assert_any_call("\n--- Stored Repositories ---")
        mock_print.assert_any_call("- Name: repoX, Path: /path/X")
        mock_print.assert_any_call("- Name: repoY, Path: /path/Y")
        mock_print.assert_any_call("--- End of Stored Repositories ---\n")


class TestRepoOperations(unittest.TestCase):
    def setUp(self):
        # Ensure a clean slate for config file if tests interact with it
        # Though these tests primarily mock interactions
        if os.path.exists(ggs.REPO_CONFIG_FILE):
            os.remove(ggs.REPO_CONFIG_FILE)
        # Store original sys.stdout to restore it, useful if redirecting for some tests
        self.original_stdout = sys.stdout
        # Redirect stdout for tests that generate a lot of print statements we want to suppress
        sys.stdout = MagicMock()


    def tearDown(self):
        if os.path.exists(ggs.REPO_CONFIG_FILE):
            os.remove(ggs.REPO_CONFIG_FILE)
        sys.stdout = self.original_stdout # Restore stdout

    @patch('git_github_starter.Repo') # Mocking Repo from git module, accessed via ggs
    def test_is_valid_git_repo_existing_repo(self, mock_repo_class):
        """Test is_valid_git_repo for an existing repository."""
        # mock_repo_instance = mock_repo_class.return_value -> This is if Repo() itself is called
        # Here, Repo(repo_path) is called. So, the class itself is what we patched.
        # We don't need to do anything with the mock_repo_class instance itself for this test,
        # as its mere successful instantiation (no InvalidGitRepositoryError) means it's valid.
        result_tuple = ggs.is_valid_git_repo("/fake/path")
        self.assertEqual(result_tuple, (True, False))
        mock_repo_class.assert_called_once_with("/fake/path")

    @patch('git_github_starter.Repo.init')
    @patch('git_github_starter.Repo') # To mock the initial Repo(path) call that fails
    @patch('builtins.input')
    @patch('os.path.join', return_value='/fake/path/.gitkeep') # Mock os.path.join
    @patch('builtins.open', new_callable=mock_open) # Mock open for .gitkeep
    def test_is_valid_git_repo_initialize_new_no_commit(self, mock_file_open, mock_os_join, mock_input, mock_repo_class, mock_repo_init):
        """Test initializing a new repo, user declines initial commit."""
        # First Repo(path) call raises InvalidGitRepositoryError
        mock_repo_class.side_effect = ggs.InvalidGitRepositoryError("test error")

        # Mock user inputs: 'y' to initialize, 'n' to commit
        mock_input.side_effect = ['y', 'n']

        # Mock Repo.init() to return a mock repo object which has an 'index' attribute
        mock_initialized_repo = MagicMock()
        mock_repo_init.return_value = mock_initialized_repo

        is_valid, was_newly_initialized = ggs.is_valid_git_repo("/fake/path")

        self.assertTrue(is_valid)
        self.assertTrue(was_newly_initialized)
        mock_repo_class.assert_called_once_with("/fake/path") # First attempt
        mock_repo_init.assert_called_once_with("/fake/path") # Initialization call
        self.assertEqual(mock_input.call_count, 2)
        mock_initialized_repo.index.commit.assert_not_called() # Commit should not be called

    @patch('git_github_starter.Repo.init')
    @patch('git_github_starter.Repo') # To mock the initial Repo(path) call that fails
    @patch('builtins.input')
    @patch('os.path.join', return_value='/fake/path/.gitkeep')
    @patch('builtins.open', new_callable=mock_open)
    def test_is_valid_git_repo_initialize_new_with_commit(self, mock_file_open, mock_os_join, mock_input, mock_repo_class, mock_repo_init):
        """Test initializing a new repo with an initial commit."""
        mock_repo_class.side_effect = ggs.InvalidGitRepositoryError("test error")
        mock_input.side_effect = ['y', 'y'] # 'y' to init, 'y' to commit

        mock_initialized_repo = MagicMock()
        mock_initialized_repo.index = MagicMock() # Mock the index object
        mock_repo_init.return_value = mock_initialized_repo

        is_valid, was_newly_initialized = ggs.is_valid_git_repo("/fake/path")

        self.assertTrue(is_valid)
        self.assertTrue(was_newly_initialized)
        mock_repo_init.assert_called_once_with("/fake/path")
        mock_file_open.assert_called_once_with('/fake/path/.gitkeep', 'a') # Check .gitkeep creation
        mock_initialized_repo.index.add.assert_called_once_with(['.gitkeep'])
        mock_initialized_repo.index.commit.assert_called_once_with("Initial commit (created .gitkeep)")
        self.assertEqual(mock_input.call_count, 2)

    @patch('git_github_starter.Repo')
    @patch('builtins.input', return_value='n') # User declines initialization
    def test_is_valid_git_repo_decline_initialization(self, mock_input, mock_repo_class):
        """Test when user declines to initialize a new repository."""
        mock_repo_class.side_effect = ggs.InvalidGitRepositoryError("test error")

        is_valid, was_newly_initialized = ggs.is_valid_git_repo("/fake/path")

        self.assertFalse(is_valid)
        self.assertFalse(was_newly_initialized)
        mock_input.assert_called_once() # Only the init prompt

    @patch('git_github_starter.Repo.clone_from')
    @patch('builtins.input')
    def test_clone_repository_by_url_success_no_save_config(self, mock_input, mock_clone_from):
        """Test clone_repository by URL, successful clone, user declines to save to config."""
        # User inputs: '1' for URL, URL, local path
        mock_input.side_effect = ['1', 'http://example.com/repo.git', '/clone/path']

        result_path = ggs.clone_repository("dummy_token")

        self.assertEqual(result_path, '/clone/path')
        mock_clone_from.assert_called_once_with('http://example.com/repo.git', '/clone/path')
        # Ensure add_repo_to_config was not called
        # This requires add_repo_to_config to be mockable or to check side effects (like file existence)
        # For now, assuming direct check of calls on input is enough for this part
        # If add_repo_to_config was imported as 'from git_github_starter import add_repo_to_config'
        # then @patch('git_github_starter.add_repo_to_config') would be needed.
        # Since we do 'import git_github_starter as ggs', ggs.add_repo_to_config is the path to patch
        with patch('git_github_starter.add_repo_to_config') as mock_add_config:
             # Re-run relevant part or structure test to isolate this check
            mock_input.side_effect = ['1', 'http://example.com/repo.git', '/clone/path', 'n'] # 'n' to save
            # This test is slightly flawed in structure as it re-runs. Better to separate.
            # For now, let's assume the prompt for saving is part of the main function using clone_repository
            # The clone_repository function itself does not ask to save. That's in main.
            # So, for unit testing clone_repository, we only test up to the clone_from call and return.
            # The config saving part will be tested in TestMainFunction.
            pass


    @patch('git_github_starter.Repo.clone_from')
    @patch('builtins.input', side_effect=['1', 'http://example.com/repo.git', '/clone/path'])
    def test_clone_repository_by_url_success(self, mock_input, mock_clone_from):
        """Test clone_repository by URL, successful clone."""
        result_path = ggs.clone_repository("dummy_token")
        self.assertEqual(result_path, '/clone/path')
        mock_clone_from.assert_called_once_with('http://example.com/repo.git', '/clone/path')

    @patch('git_github_starter.Repo.clone_from', side_effect=ggs.GitCommandError("clone", "failed"))
    @patch('builtins.input', side_effect=['1', 'http://example.com/repo.git', '/clone/path'])
    def test_clone_repository_by_url_failure(self, mock_input, mock_clone_from):
        """Test clone_repository by URL, cloning fails."""
        result_path = ggs.clone_repository("dummy_token")
        self.assertIsNone(result_path)
        mock_clone_from.assert_called_once_with('http://example.com/repo.git', '/clone/path')

    @patch('git_github_starter.Github')
    @patch('git_github_starter.Repo.clone_from')
    @patch('builtins.input')
    def test_clone_repository_by_github_list_success(self, mock_input, mock_clone_from, mock_github_api):
        """Test cloning by selecting from GitHub repo list."""
        # Setup mock GitHub API
        mock_gh_instance = MagicMock()
        mock_user = MagicMock()
        mock_repo1 = MagicMock()
        mock_repo1.full_name = "user/repo1"
        mock_repo1.clone_url = "http://github.com/user/repo1.git"
        mock_user.get_repos.return_value = [mock_repo1]
        mock_gh_instance.get_user.return_value = mock_user
        mock_github_api.return_value = mock_gh_instance

        # User inputs: '2' for GitHub list, '1' to select first repo, '/clone/to/path'
        mock_input.side_effect = ['2', '1', '/clone/to/path']

        result_path = ggs.clone_repository("fake_token")

        self.assertEqual(result_path, '/clone/to/path')
        mock_github_api.assert_called_once_with("fake_token")
        mock_clone_from.assert_called_once_with("http://github.com/user/repo1.git", '/clone/to/path')

    @patch('git_github_starter.Github')
    @patch('builtins.input', side_effect=['2']) # Choose list, but no token
    def test_clone_repository_by_github_list_no_token(self, mock_input, mock_github_api):
        """Test cloning from GitHub list when no token is provided to clone_repository."""
        result_path = ggs.clone_repository(None) # Pass None as github_token
        self.assertIsNone(result_path)
        mock_github_api.assert_not_called() # Github should not be initialized

    @patch('git_github_starter.Github')
    @patch('builtins.input')
    def test_clone_repository_by_github_list_api_error(self, mock_input, mock_github_api):
        """Test cloning from GitHub list with a GithubException."""
        mock_github_api.side_effect = ggs.GithubException(status=401, data="Unauthorized", headers=None)
        # User inputs: '2' for GitHub list
        mock_input.side_effect = ['2']

        result_path = ggs.clone_repository("bad_token")
        self.assertIsNone(result_path)

class TestMainFunction(unittest.TestCase):
    def setUp(self):
        # Common mocks needed for many main() logic tests
        self.mock_argparse = patch('argparse.ArgumentParser').start()
        self.mock_parse_args = self.mock_argparse.return_value.parse_args

        # Mock functions from ggs module that main calls
        self.mock_list_repos_from_config = patch('git_github_starter.list_repos_from_config').start()
        self.mock_clone_repository = patch('git_github_starter.clone_repository').start()
        self.mock_is_valid_git_repo = patch('git_github_starter.is_valid_git_repo').start()
        self.mock_add_repo_to_config = patch('git_github_starter.add_repo_to_config').start()
        self.mock_get_repo_path_from_config = patch('git_github_starter.get_repo_path_from_config').start()
        self.mock_get_github_repo_from_local = patch('git_github_starter.get_github_repo_from_local').start()
        self.mock_github_repo_exists = patch('git_github_starter.github_repo_exists').start()
        self.mock_check_git_status_and_commit = patch('git_github_starter.check_git_status_and_commit').start()
        self.mock_get_repository_info = patch('git_github_starter.get_repository_info').start()
        self.mock_create_github_issue = patch('git_github_starter.create_github_issue').start()

        patch('builtins.print').start() # Suppress prints from main
        self.mock_sys_exit = patch('sys.exit').start()

        # Ensure a clean config file for tests that might interact via called functions
        if os.path.exists(ggs.REPO_CONFIG_FILE):
            os.remove(ggs.REPO_CONFIG_FILE)


    def tearDown(self):
        patch.stopall()
        if os.path.exists(ggs.REPO_CONFIG_FILE):
            os.remove(ggs.REPO_CONFIG_FILE)

    def test_main_list_repos_action(self):
        """Test main() when 'list_repos' argument is provided."""
        self.mock_parse_args.return_value = MagicMock(
            list_repos=True, clone_repo=False, repo_name=None, local_path=None, init_repo=False, github_repo=None
        )
        ggs.main()
        self.mock_list_repos_from_config.assert_called_once()
        self.mock_sys_exit.assert_called_once_with(0)

    def test_main_clone_repo_success_and_save(self):
        """Test main() for --clone-repo, successful clone, and user saves to config."""
        self.mock_parse_args.return_value = MagicMock(
            list_repos=False, clone_repo=True, repo_name=None, local_path=None, init_repo=False, github_repo="user/cloned"
        )
        self.mock_clone_repository.return_value = "/cloned/path" # Successful clone
        self.mock_is_valid_git_repo.return_value = (True, False) # Assume cloned repo is valid
        self.mock_github_repo_exists.return_value = True

        with patch('builtins.input', side_effect=['y', 'cloned_repo_name']): # Save to config, provide name
            ggs.main()

        self.mock_clone_repository.assert_called_once_with(ggs.GITHUB_TOKEN)
        self.mock_add_repo_to_config.assert_called_once_with("cloned_repo_name", "/cloned/path")
        self.mock_check_git_status_and_commit.assert_called_once_with("/cloned/path")
        # Further checks for get_repository_info etc. can be added if GITHUB_TOKEN is assumed present

    def test_main_clone_repo_failure(self):
        """Test main() for --clone-repo when cloning fails."""
        self.mock_parse_args.return_value = MagicMock(clone_repo=True, list_repos=False, repo_name=None, local_path=None, init_repo=False)
        self.mock_clone_repository.return_value = None # Cloning fails

        ggs.main()

        self.mock_clone_repository.assert_called_once_with(ggs.GITHUB_TOKEN)
        self.mock_sys_exit.assert_called_once_with(1)

    def test_main_init_repo_success_and_save(self):
        """Test main() for --init-repo, successful init, and user saves to config."""
        self.mock_parse_args.return_value = MagicMock(
            init_repo=True, local_path="/new/repo/path", list_repos=False, clone_repo=False, repo_name=None, github_repo="user/newrepo"
        )
        self.mock_is_valid_git_repo.return_value = (True, True) # Valid, was newly initialized
        self.mock_github_repo_exists.return_value = True

        with patch('builtins.input', side_effect=['y', 'new_repo_config_name']): # Save to config, provide name
            ggs.main()

        self.mock_is_valid_git_repo.assert_called_once_with("/new/repo/path")
        self.mock_add_repo_to_config.assert_called_once_with("new_repo_config_name", "/new/repo/path")
        self.mock_check_git_status_and_commit.assert_called_once_with("/new/repo/path")

    def test_main_use_repo_name_from_config(self):
        """Test main() when --repo-name is used."""
        self.mock_parse_args.return_value = MagicMock(
            repo_name="my_config_repo", list_repos=False, clone_repo=False, init_repo=False, local_path=None, github_repo=None
        )
        self.mock_get_repo_path_from_config.return_value = "/config/path/my_repo"
        self.mock_is_valid_git_repo.return_value = (True, False) # Existing valid repo
        self.mock_get_github_repo_from_local.return_value = "user/fromlocal" # Auto-detected GitHub name
        self.mock_github_repo_exists.return_value = True

        ggs.main()

        self.mock_get_repo_path_from_config.assert_called_once_with("my_config_repo")
        self.mock_is_valid_git_repo.assert_called_once_with("/config/path/my_repo")
        self.mock_check_git_status_and_commit.assert_called_once_with("/config/path/my_repo")
        self.mock_get_github_repo_from_local.assert_called_once_with("/config/path/my_repo")
        self.mock_github_repo_exists.assert_called_once_with(ggs.GITHUB_TOKEN, "user/fromlocal")


    def test_main_repo_name_not_in_config(self):
        """Test main() when --repo-name is used but name not in config."""
        self.mock_parse_args.return_value = MagicMock(repo_name="non_existent", list_repos=False, clone_repo=False, init_repo=False, local_path=None)
        self.mock_get_repo_path_from_config.return_value = None # Name not found

        ggs.main()

        self.mock_get_repo_path_from_config.assert_called_once_with("non_existent")
        self.mock_sys_exit.assert_called_once_with(1)

    def test_main_local_path_provided_no_github_repo_arg_prompts_for_github_name(self):
        """Test main() when --local-path is given, --github-repo is not, and auto-detection fails."""
        self.mock_parse_args.return_value = MagicMock(
            local_path="/given/path", github_repo=None, list_repos=False, clone_repo=False, repo_name=None, init_repo=False
        )
        self.mock_is_valid_git_repo.return_value = (True, False) # Valid, existing
        self.mock_get_github_repo_from_local.return_value = None # Auto-detection fails
        self.mock_github_repo_exists.return_value = True # Assume user provides valid one

        with patch('builtins.input', return_value="user/typedname"): # User types GitHub name
            ggs.main()

        self.mock_is_valid_git_repo.assert_called_once_with("/given/path")
        self.mock_get_github_repo_from_local.assert_called_once_with("/given/path")
        self.assertEqual(self.mock_github_repo_exists.call_args[0][1], "user/typedname") # Check second arg of call
        self.mock_check_git_status_and_commit.assert_called_once_with("/given/path")


# More test classes will be added here for other functionalities

class TestGitHubRepoCreationAndRemoteSetup(unittest.TestCase):
    def setUp(self):
        self.mock_github_class = patch('git_github_starter.Github').start()
        self.mock_gh_instance = self.mock_github_class.return_value
        self.mock_user = MagicMock()
        self.mock_gh_instance.get_user.return_value = self.mock_user

        self.mock_repo_class = patch('git_github_starter.Repo').start()
        self.mock_repo_instance = self.mock_repo_class.return_value
        
        # Mock sys.exit to prevent tests from stopping prematurely
        self.mock_sys_exit = patch('sys.exit').start()
        # Mock print to suppress output unless specifically desired
        self.mock_print = patch('builtins.print').start()

        # Mock GITHUB_TOKEN if it's checked directly
        patch.dict(ggs.os.environ, {"GITHUB_TOKEN": "test_token"}, clear=True).start()
        ggs.GITHUB_TOKEN = "test_token" # Ensure module's global is also set for the test


    def tearDown(self):
        patch.stopall()
        ggs.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Restore original GITHUB_TOKEN logic

    def test_create_github_repository_success(self):
        mock_new_repo = MagicMock()
        mock_new_repo.html_url = "http://github.com/user/newrepo"
        mock_new_repo.full_name = "user/newrepo"
        self.mock_user.create_repo.return_value = mock_new_repo
        self.mock_user.login = "user"

        repo_obj = ggs.create_github_repository("test_token", "user/newrepo", description="A new repo", private=True)

        self.mock_user.create_repo.assert_called_once_with(
            "newrepo", description="A new repo", private=True, auto_init=False
        )
        self.assertEqual(repo_obj, mock_new_repo)
        self.mock_print.assert_any_call(f"Successfully created GitHub repository: {mock_new_repo.html_url}")

    def test_create_github_repository_api_error_already_exists(self):
        self.mock_user.create_repo.side_effect = ggs.GithubException(status=422, data={"message": "Repo already exists"}, headers=None)
        self.mock_user.login = "user"
        
        repo_obj = ggs.create_github_repository("test_token", "user/existingrepo")
        
        self.assertIsNone(repo_obj)
        self.mock_print.assert_any_call(f"GitHub API error during repository creation for 'user/existingrepo': 422 {{'message': 'Repo already exists'}}")
        self.mock_print.assert_any_call("This might mean the repository already exists or the name is invalid.")

    def test_create_github_repository_username_mismatch_warning(self):
        self.mock_user.login = "actual_user"
        mock_new_repo = MagicMock()
        mock_new_repo.html_url = "http://github.com/actual_user/repo"
        self.mock_user.create_repo.return_value = mock_new_repo

        ggs.create_github_repository("test_token", "provided_user/repo")
        
        self.mock_print.assert_any_call(f"Warning: Provided username 'provided_user' in 'provided_user/repo' does not match authenticated user 'actual_user'. Repository will be created under 'actual_user'.")
        self.mock_user.create_repo.assert_called_with("repo", description="", private=False, auto_init=False)

    def test_create_github_repository_no_token(self):
        repo_obj = ggs.create_github_repository(None, "user/repo")
        self.assertIsNone(repo_obj)
        self.mock_print.assert_any_call("Error: GitHub token is required to create a repository.")

    def test_setup_remote_origin_new_remote(self):
        # Mock remote() to initially raise ValueError, then return the origin mock after creation
        mock_origin = MagicMock()
        mock_origin.url = "new_url" # So config_writer can be called on it
        self.mock_repo_instance.remote.side_effect = [ValueError, mock_origin] # First call fails, second succeeds
        self.mock_repo_instance.create_remote.return_value = mock_origin
        
        # Mock branches/heads
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_branch.commit = "some_commit_sha" # Has commits
        self.mock_repo_instance.heads = [mock_branch] # Make it iterable and indexable
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_branch if key == "main" else (_ for _ in ()).throw(IndexError)


        success = ggs.setup_remote_origin("/fake/path", "http://github.com/user/newrepo.git", default_branch_name="main")

        self.assertTrue(success)
        self.mock_repo_instance.create_remote.assert_called_once_with('origin', "http://github.com/user/newrepo.git")
        mock_origin.push.assert_called_once_with(refspec="main:main", set_upstream=True)

    def test_setup_remote_origin_existing_remote(self):
        mock_origin = MagicMock()
        mock_origin.url = "old_url"
        # mock_origin.set_url = MagicMock() # set_url is on the remote itself
        self.mock_repo_instance.remote.return_value = mock_origin
        
        # Mock config_writer context manager
        mock_config_writer = MagicMock()
        mock_origin.config_writer = mock_config_writer
        mock_cw_instance = mock_config_writer.__enter__.return_value # what 'cw' becomes
        
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_branch.commit = "some_commit_sha"
        self.mock_repo_instance.heads = [mock_branch]
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_branch if key == "main" else (_ for _ in ()).throw(IndexError)


        success = ggs.setup_remote_origin("/fake/path", "http://github.com/user/updatedrepo.git", default_branch_name="main")

        self.assertTrue(success)
        self.mock_repo_instance.remote.assert_called_with(name='origin')
        # self.assertEqual(mock_origin.url, "http://github.com/user/updatedrepo.git") # This is tricky with context manager
        mock_cw_instance.set.assert_called_once_with("url", "http://github.com/user/updatedrepo.git")
        mock_origin.push.assert_called_once_with(refspec="main:main", set_upstream=True)


    def test_setup_remote_origin_no_commits(self):
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_branch.commit = None # No commits on the branch
        self.mock_repo_instance.heads = [mock_branch]
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_branch if key == "main" else (_ for _ in ()).throw(IndexError)


        success = ggs.setup_remote_origin("/fake/path", "http://url.git")
        self.assertFalse(success)
        self.mock_print.assert_any_call(f"Error: Branch 'main' in '/fake/path' has no commits. Cannot push.")

    def test_setup_remote_origin_push_error(self):
        mock_origin = MagicMock()
        self.mock_repo_instance.remote.return_value = mock_origin
        mock_origin.push.side_effect = ggs.GitCommandError("push", "failed")
        
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_branch.commit = "some_commit_sha"
        self.mock_repo_instance.heads = [mock_branch]
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_branch if key == "main" else (_ for _ in ()).throw(IndexError)


        success = ggs.setup_remote_origin("/fake/path", "http://url.git")
        self.assertFalse(success)
        self.mock_print.assert_any_call("Git command error during remote setup for '/fake/path': Cmd('push') failed: failed")

    # Tests for main() logic related to --create-github-repo
    @patch('git_github_starter.github_repo_exists')
    @patch('git_github_starter.create_github_repository')
    @patch('git_github_starter.setup_remote_origin')
    @patch('git_github_starter.is_valid_git_repo') # Assume local repo is valid
    @patch('argparse.ArgumentParser') # To control args
    def test_main_create_github_repo_success(self, mock_argparse_class, mock_is_valid, mock_setup_remote, mock_create_repo, mock_repo_exists):
        mock_args = MagicMock(
            create_github_repo=True, github_repo="user/newrepo", local_path="/fake/path",
            fetch=False, list_branches=False, checkout=None, create_branch=None, pull=False, # other args
            list_repos=False, clone_repo=False, repo_name=None, init_repo=False # original other args
        )
        mock_argparse_class.return_value.parse_args.return_value = mock_args
        
        mock_repo_exists.return_value = False # GitHub repo does not exist
        mock_created_gh_repo = MagicMock()
        mock_created_gh_repo.full_name = "user/newrepo"
        mock_created_gh_repo.clone_url = "http://github.com/user/newrepo.git"
        mock_create_repo.return_value = mock_created_gh_repo
        mock_setup_remote.return_value = True
        mock_is_valid.return_value = (True, False) # Local repo is valid

        # Mock active branch for setup_remote_origin call in main
        mock_local_repo_instance_for_branch = MagicMock()
        mock_active_branch = MagicMock()
        mock_active_branch.name = "main"
        mock_active_branch.commit = "sha123" # Has a commit
        mock_local_repo_instance_for_branch.active_branch = mock_active_branch
        mock_local_repo_instance_for_branch.head.is_valid.return_value = True
        
        # When Repo(local_repo_path_input) is called inside main for branch check
        self.mock_repo_class.return_value = mock_local_repo_instance_for_branch


        ggs.main()

        mock_create_repo.assert_called_once_with(ggs.GITHUB_TOKEN, "user/newrepo", description=f"Repository user/newrepo created by git_github_starter.py", private=False)
        mock_setup_remote.assert_called_once_with("/fake/path", "http://github.com/user/newrepo.git", default_branch_name="main")
        self.mock_sys_exit.assert_not_called()


    @patch('git_github_starter.github_repo_exists')
    @patch('git_github_starter.create_github_repository')
    @patch('git_github_starter.is_valid_git_repo')
    @patch('argparse.ArgumentParser')
    def test_main_create_github_repo_creation_fails(self, mock_argparse_class, mock_is_valid, mock_create_repo, mock_repo_exists):
        mock_args = MagicMock(create_github_repo=True, github_repo="user/failrepo", local_path="/fake/path", fetch=False, list_branches=False, checkout=None, create_branch=None, pull=False, list_repos=False, clone_repo=False, repo_name=None, init_repo=False)
        mock_argparse_class.return_value.parse_args.return_value = mock_args
        
        mock_repo_exists.return_value = False
        mock_create_repo.return_value = None # Creation fails
        mock_is_valid.return_value = (True, False)

        ggs.main()
        
        mock_create_repo.assert_called_once()
        self.mock_sys_exit.assert_called_once_with(1)

    @patch('git_github_starter.github_repo_exists')
    @patch('git_github_starter.create_github_repository')
    @patch('git_github_starter.setup_remote_origin')
    @patch('git_github_starter.is_valid_git_repo')
    @patch('argparse.ArgumentParser')
    def test_main_create_github_repo_setup_remote_fails(self, mock_argparse_class, mock_is_valid, mock_setup_remote, mock_create_repo, mock_repo_exists):
        mock_args = MagicMock(create_github_repo=True, github_repo="user/remotefail", local_path="/fake/path", fetch=False, list_branches=False, checkout=None, create_branch=None, pull=False, list_repos=False, clone_repo=False, repo_name=None, init_repo=False)
        mock_argparse_class.return_value.parse_args.return_value = mock_args

        mock_repo_exists.return_value = False
        mock_created_gh_repo = MagicMock(clone_url="http://url.git", full_name="user/remotefail")
        mock_create_repo.return_value = mock_created_gh_repo
        mock_setup_remote.return_value = False # Setup remote fails
        mock_is_valid.return_value = (True, False)
        
        # Mock for active branch check in main
        mock_local_repo_instance_for_branch = MagicMock()
        mock_active_branch = MagicMock(name="main", commit="sha123")
        mock_local_repo_instance_for_branch.active_branch = mock_active_branch
        mock_local_repo_instance_for_branch.head.is_valid.return_value = True
        self.mock_repo_class.return_value = mock_local_repo_instance_for_branch

        ggs.main()
        
        mock_create_repo.assert_called_once()
        mock_setup_remote.assert_called_once()
        self.mock_sys_exit.assert_called_once_with(1)

    @patch('git_github_starter.github_repo_exists')
    @patch('git_github_starter.is_valid_git_repo')
    @patch('argparse.ArgumentParser')
    def test_main_create_github_repo_no_token(self, mock_argparse_class, mock_is_valid, mock_repo_exists):
        # Temporarily unset GITHUB_TOKEN for this test
        original_token = ggs.GITHUB_TOKEN
        ggs.GITHUB_TOKEN = None
        patch.dict(ggs.os.environ, {"GITHUB_TOKEN": ""}, clear=True).start()


        mock_args = MagicMock(create_github_repo=True, github_repo="user/notoken", local_path="/fake/path", fetch=False, list_branches=False, checkout=None, create_branch=None, pull=False, list_repos=False, clone_repo=False, repo_name=None, init_repo=False)
        mock_argparse_class.return_value.parse_args.return_value = mock_args
        
        mock_repo_exists.return_value = False # Repo doesn't exist
        mock_is_valid.return_value = (True, False)

        ggs.main()
        
        self.mock_print.assert_any_call("Error: --create-github-repo requires GITHUB_TOKEN to be set. Exiting.")
        self.mock_sys_exit.assert_called_once_with(1)
        
        ggs.GITHUB_TOKEN = original_token # Restore for other tests
        patch.stopall() # Stop the os.environ patch specifically for this test


class TestGitExtendedOperations(unittest.TestCase):
    def setUp(self):
        self.mock_repo_class = patch('git_github_starter.Repo').start()
        self.mock_repo_instance = self.mock_repo_class.return_value
        self.mock_origin = MagicMock(name="origin")
        self.mock_repo_instance.remote.return_value = self.mock_origin
        
        self.mock_print = patch('builtins.print').start()
        self.mock_sys_exit = patch('sys.exit').start()

    def tearDown(self):
        patch.stopall()

    # Tests for fetch_changes
    def test_fetch_changes_success(self):
        mock_fetch_info = [MagicMock(name='origin/main', summary='summary', flags=0)]
        self.mock_origin.fetch.return_value = mock_fetch_info
        self.mock_origin.exists.return_value = True

        result = ggs.fetch_changes("/fake/path")
        self.assertTrue(result)
        self.mock_origin.fetch.assert_called_once()
        self.mock_print.assert_any_call(f"Fetched: origin/main, Summary: summary, Flags: 0")

    def test_fetch_changes_no_origin(self):
        self.mock_origin.exists.return_value = False
        result = ggs.fetch_changes("/fake/path")
        self.assertFalse(result)
        self.mock_print.assert_any_call("Error: Remote 'origin' does not exist in /fake/path.")

    def test_fetch_changes_git_command_error(self):
        self.mock_origin.exists.return_value = True
        self.mock_origin.fetch.side_effect = ggs.GitCommandError("fetch", "failed")
        result = ggs.fetch_changes("/fake/path")
        self.assertFalse(result)
        self.mock_print.assert_any_call("Git command error during fetch: Cmd('fetch') failed: failed")

    # Tests for list_branches
    def test_list_branches_success(self):
        self.mock_repo_instance.heads = [MagicMock(name="main"), MagicMock(name="dev")]
        mock_remote_ref_main = MagicMock(name="origin/main")
        mock_remote_ref_feature = MagicMock(name="origin/feature-branch")
        # Mock tracking for main branch
        self.mock_repo_instance.heads[0].tracking_branch.return_value = mock_remote_ref_main
        self.mock_repo_instance.heads[1].tracking_branch.return_value = None # dev branch doesn't track

        self.mock_origin.exists.return_value = True
        self.mock_origin.refs = [mock_remote_ref_main, mock_remote_ref_feature, MagicMock(name="origin/HEAD")]
        
        ggs.list_branches("/fake/path")
        
        self.mock_print.assert_any_call("  - main")
        self.mock_print.assert_any_call("  - dev")
        self.mock_print.assert_any_call("  - origin/main")
        self.mock_print.assert_any_call("    (tracked by local: main)")
        self.mock_print.assert_any_call("  - origin/feature-branch")
        self.mock_origin.fetch.assert_called_once() # Called to update refs

    def test_list_branches_no_origin(self):
        self.mock_origin.exists.return_value = False
        ggs.list_branches("/fake/path")
        self.mock_print.assert_any_call("  Remote 'origin' does not exist.")

    # Tests for checkout_branch
    def test_checkout_branch_create_new_success(self):
        self.mock_repo_instance.heads = {} # No existing branches by that name
        mock_new_branch_head = MagicMock(name="new_feature")
        self.mock_repo_instance.create_head.return_value = mock_new_branch_head
        
        result = ggs.checkout_branch("/fake/path", "new_feature", create_new=True)
        
        self.assertTrue(result)
        self.mock_repo_instance.create_head.assert_called_once_with("new_feature")
        mock_new_branch_head.checkout.assert_called_once()
        self.mock_print.assert_any_call("Created and checked out new branch: new_feature")

    def test_checkout_branch_create_new_already_exists(self):
        self.mock_repo_instance.heads = {"existing_feature": MagicMock()}
        result = ggs.checkout_branch("/fake/path", "existing_feature", create_new=True)
        self.assertFalse(result)
        self.mock_print.assert_any_call("Error: Branch 'existing_feature' already exists. Cannot create.")

    def test_checkout_branch_local_existing(self):
        mock_local_branch = MagicMock(name="local_dev")
        self.mock_repo_instance.heads = {"local_dev": mock_local_branch}
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_local_branch if key == "local_dev" else MagicMock()

        result = ggs.checkout_branch("/fake/path", "local_dev")
        self.assertTrue(result)
        mock_local_branch.checkout.assert_called_once()

    def test_checkout_remote_branch_create_tracking(self):
        self.mock_repo_instance.heads = {} # No local branch with that name
        self.mock_origin.exists.return_value = True
        mock_remote_ref = MagicMock(name="origin/feature_x", remote_head="feature_x")
        self.mock_origin.refs = [mock_remote_ref]
        
        mock_new_tracking_head = MagicMock(name="feature_x")
        self.mock_repo_instance.create_head.return_value = mock_new_tracking_head

        result = ggs.checkout_branch("/fake/path", "feature_x") # User provides 'feature_x'
        
        self.assertTrue(result)
        self.mock_repo_instance.create_head.assert_called_once_with("feature_x", mock_remote_ref)
        mock_new_tracking_head.set_tracking_branch.assert_called_once_with(mock_remote_ref)
        mock_new_tracking_head.checkout.assert_called_once()

    def test_checkout_remote_branch_already_tracks(self):
        mock_local_feature_x = MagicMock(name="feature_x")
        mock_remote_ref_feature_x = MagicMock(name="origin/feature_x", remote_head="feature_x")
        mock_local_feature_x.tracking_branch.return_value = mock_remote_ref_feature_x # It tracks the correct remote
        
        self.mock_repo_instance.heads = {"feature_x": mock_local_feature_x}
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_local_feature_x if key == "feature_x" else MagicMock()
        self.mock_origin.exists.return_value = True
        self.mock_origin.refs = [mock_remote_ref_feature_x] # Remote branch exists

        result = ggs.checkout_branch("/fake/path", "feature_x") # Try to checkout 'feature_x'
        
        self.assertTrue(result)
        mock_local_feature_x.checkout.assert_called_once()
        self.mock_print.assert_any_call("Local branch 'feature_x' already tracks 'origin/feature_x'. Checking it out.")

    def test_checkout_remote_branch_local_exists_does_not_track(self):
        mock_local_feature_x = MagicMock(name="feature_x")
        mock_local_feature_x.tracking_branch.return_value = None # Does not track anything
        
        mock_remote_ref_feature_x = MagicMock(name="origin/feature_x", remote_head="feature_x")
        
        self.mock_repo_instance.heads = {"feature_x": mock_local_feature_x}
        self.mock_repo_instance.heads.__getitem__.side_effect = lambda key: mock_local_feature_x if key == "feature_x" else MagicMock()

        self.mock_origin.exists.return_value = True
        self.mock_origin.refs = [mock_remote_ref_feature_x]

        result = ggs.checkout_branch("/fake/path", "feature_x")
        self.assertFalse(result)
        self.mock_print.assert_any_call("Error: Local branch 'feature_x' exists but does not track 'origin/feature_x'.")

    def test_checkout_branch_not_found(self):
        self.mock_repo_instance.heads = {}
        self.mock_origin.exists.return_value = True
        self.mock_origin.refs = [] # No remote branches match

        result = ggs.checkout_branch("/fake/path", "non_existent_branch")
        self.assertFalse(result)
        self.mock_print.assert_any_call("Error: Branch 'non_existent_branch' not found as a local branch, and 'origin/non_existent_branch' not found on remote 'origin'.")

    # Tests for pull_changes
    def test_pull_changes_success(self):
        self.mock_repo_instance.is_dirty.return_value = False
        self.mock_origin.exists.return_value = True
        mock_active_branch = MagicMock(name="main")
        mock_tracking_branch = MagicMock(remote_name="origin", remote_head="main")
        mock_active_branch.tracking_branch.return_value = mock_tracking_branch
        self.mock_repo_instance.active_branch = mock_active_branch
        
        mock_pull_info = [MagicMock(name='origin/main', ref='refs/heads/main', summary='Pulled changes', flags=0)]
        self.mock_origin.pull.return_value = mock_pull_info

        result = ggs.pull_changes("/fake/path")
        self.assertTrue(result)
        self.mock_origin.pull.assert_called_once()

    def test_pull_changes_repo_dirty(self):
        self.mock_repo_instance.is_dirty.return_value = True
        # Function might still return True after warning, or False if it decides to stop
        # Current implementation just warns, so it would proceed.
        # Let's assume it would try to proceed but we only check the warning here.
        ggs.pull_changes("/fake/path")
        self.mock_print.assert_any_call("Warning: Repository has uncommitted changes. Please commit or stash them before pulling.")

    def test_pull_changes_no_tracking_branch(self):
        self.mock_repo_instance.is_dirty.return_value = False
        self.mock_origin.exists.return_value = True
        mock_active_branch = MagicMock(name="main")
        mock_active_branch.tracking_branch.return_value = None # Not tracking
        self.mock_repo_instance.active_branch = mock_active_branch

        result = ggs.pull_changes("/fake/path")
        self.assertFalse(result)
        self.mock_print.assert_any_call(f"Error: Current branch 'main' is not tracking any remote branch. Cannot pull.")

    def test_pull_changes_git_command_error_merge_conflict(self):
        self.mock_repo_instance.is_dirty.return_value = False
        self.mock_origin.exists.return_value = True
        mock_active_branch = MagicMock(name="main")
        mock_tracking_branch = MagicMock(remote_name="origin", remote_head="main")
        mock_active_branch.tracking_branch.return_value = mock_tracking_branch
        self.mock_repo_instance.active_branch = mock_active_branch
        
        self.mock_origin.pull.side_effect = ggs.GitCommandError("pull", "Merge conflict occurred")

        result = ggs.pull_changes("/fake/path")
        self.assertFalse(result)
        self.mock_print.assert_any_call("MERGE CONFLICT DETECTED. Please resolve conflicts manually.")


if __name__ == '__main__':
    unittest.main()
