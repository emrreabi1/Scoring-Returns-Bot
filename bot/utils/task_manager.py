class TaskManager:
    def __init__(self):
        # Initialize a dictionary to keep track of user tasks
        self.user_tasks = {}  # Dictionary mapping user IDs to tuples (task_count, [games_list])

    def new_add_task(self, user_id, game_name):
        """
        Adds a new task for a user and tracks the game they're following.
        
        Parameters:
        - user_id (int): The unique identifier for the user
        - game_name (str): The name of the game/match to track
        
        Updates self.user_tasks with (task_count, [games_list]) tuple
        """
        if user_id in self.user_tasks:
            current_info = self.user_tasks.get(user_id, (0, []))

            # Increment the number of tasks
            new_number_tasks = current_info[0] + 1

            # Add a new string to the list. Let's say the new string is "new_task_info"
            new_task_info = game_name  # This is the new string you want to add
            new_tasks_list = current_info[1] + [game_name]  # Append the new string to the existing list

            # Create a new tuple with the updated info
            new_info = (new_number_tasks, new_tasks_list)

            # Update the dictionary with the new tuple<
            self.user_tasks[user_id] = new_info
        else:

            new_task_info = game_name  # This is the new string you want to add
            new_tasks_list =[new_task_info]  # Append the new string to the existing list

            new_number_tasks = 1

            # Create a new tuple with the updated info
            new_info = (new_number_tasks, new_tasks_list)

            # Update the dictionary with the new tuple
            self.user_tasks[user_id] = new_info
            
    def new_remove_task(self, user_id, game_name):
        """
        Removes a task for a user and its associated game.
        
        Parameters:
        - user_id (int): The unique identifier for the user
        - game_name (str): The name of the game/match to remove
        
        Deletes user from self.user_tasks if their task count reaches 0
        """
        if user_id in self.user_tasks:
            current_info = self.user_tasks.get(user_id, (0, []))

            # Decrement the number of tasks
            new_number_tasks = current_info[0] - 1

            new_tasks_list = current_info[1]
            
            if game_name in new_tasks_list:
                new_tasks_list.remove(game_name)
            
            new_info = (new_number_tasks, new_tasks_list)

            # Update the dictionary with the new tuple
            self.user_tasks[user_id] = new_info
            
            if new_number_tasks <= 0:
                del self.user_tasks[user_id]

    def get_task_games_list(self, user_id):
        """
        Retrieves the list of games a user is currently tracking.
        
        Parameters:
        - user_id (int): The unique identifier for the user
        
        Returns:
        - list: List of game names the user is tracking
        """
        current_info = self.user_tasks.get(user_id, (0, []))
        current_games = current_info[1]
        
        return current_games

    def new_get_task_count(self, user_id):
        """
        Gets the number of active tasks for a user.
        
        Parameters:
        - user_id (int): The unique identifier for the user
        
        Returns:
        - int: Number of active tasks for the user
        """
        current_info = self.user_tasks.get(user_id, (0, []))
        number_of_tasks = current_info[0]
        
        return number_of_tasks
    
    
    