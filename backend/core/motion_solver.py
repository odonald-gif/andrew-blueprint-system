import logging
from typing import List, Dict, Any, Tuple
from ortools.sat.python import cp_model

logger = logging.getLogger(__name__)

class MotionSolver:
    """
    The Mathematical "Motion" Solver.
    Uses OR-Tools Constraint Programming to calculate optimal paths 
    for tasks and calendar availability, avoiding overlapping meetings 
    and respecting hard deadlines.
    """
    
    def __init__(self):
        pass

    def schedule_tasks(self, tasks: List[Dict[str, Any]], busy_slots: List[Dict[str, int]], max_time: int = 1440) -> Dict[str, Any]:
        """
        Calculates an optimal schedule for abstract tasks into a daily timeline.
        
        Args:
            tasks: List of objects containing id, duration (minutes), priority, deadline.
            busy_slots: List of existing calendar blocks with start and end times (in minutes from midnight).
            max_time: Total minutes in the day constraint (usually 1440).
            
        Returns:
            Dict containing the status and scheduled times for each task.
        """
        model = cp_model.CpModel()
        
        # We will collect task variables to evaluate
        task_vars = {}
        intervals = []
        
        # 1. Pre-populate busy slots as fixed intervals
        for i, slot in enumerate(busy_slots):
            start = slot['start']
            duration = slot['end'] - start
            end = slot['end']
            
            # Create variables that are fixed (domain is exactly the value)
            start_var = model.NewIntVar(start, start, f'busy_start_{i}')
            end_var = model.NewIntVar(end, end, f'busy_end_{i}')
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f'busy_interval_{i}')
            intervals.append(interval_var)

        # 2. Setup Task variables
        for task in tasks:
            t_id = task['id']
            duration = task['duration']
            deadline = task.get('deadline', max_time)
            
            # The start can be anywhere from 0 to deadline - duration
            start_var = model.NewIntVar(0, max_time - duration, f'task_start_{t_id}')
            end_var = model.NewIntVar(0, max_time, f'task_end_{t_id}')
            
            # An optional variable: Is this task scheduled?
            # For tasks with soft deadlines, maybe they don't get scheduled today
            # If the task MUST be completed today, we force is_present=1
            is_present = model.NewBoolVar(f'task_present_{t_id}')
            
            # Interval variable that can be optional
            interval_var = model.NewOptionalIntervalVar(
                start_var, duration, end_var, is_present, f'task_interval_{t_id}'
            )
            intervals.append(interval_var)
            
            # Ensure hard deadlines are met
            if task.get('hard_deadline', False):
                model.Add(is_present == 1)
                
            model.Add(end_var <= deadline).OnlyEnforceIf(is_present)
            
            task_vars[t_id] = {
                'start_var': start_var,
                'end_var': end_var,
                'is_present': is_present,
                'priority': task.get('priority', 1)
            }

        # 3. Add No-Overlap constraint
        model.AddNoOverlap(intervals)

        # 4. Objective: Maximize priority of scheduled tasks AND minimize the spread/delay
        objective_terms = []
        for t_id, var_dict in task_vars.items():
            # Reward for scheduling the task scaled by priority
            objective_terms.append(var_dict['priority'] * 1000 * var_dict['is_present'])
            # Minor penalty for starting later in the day to push tasks earlier
            # objective_terms.append(-1 * var_dict['start_var'])

        model.Maximize(sum(objective_terms))
        
        # 5. Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        
        result = {
            "status": solver.StatusName(status),
            "scheduled": [],
            "unscheduled": []
        }
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            for t_id, var_dict in task_vars.items():
                if solver.BooleanValue(var_dict['is_present']):
                    result["scheduled"].append({
                        "id": t_id,
                        "start": solver.Value(var_dict['start_var']),
                        "end": solver.Value(var_dict['end_var'])
                    })
                else:
                    result["unscheduled"].append(t_id)
        else:
            logger.warning("Solver failed to find a feasible schedule.")
            
        return result
