"""Poker game tools for ADK agents."""

from typing import Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext
from .game.env import HoldemTable
from .game.enums import Action
import logging
import numpy as np

log = logging.getLogger(__name__)

# Global game state - in production, this should be managed differently
game_table: Optional[HoldemTable] = None
current_game_state: Dict[str, Any] = {}


def _convert_numpy_types(obj):
    """
    Recursively convert numpy types and enum types to native Python types for serialization.

    Args:
        obj: Object that may contain numpy types or enum types

    Returns:
        Object with numpy types and enum types converted to native Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, Action):
        return obj.name  # Convert Action enum to string name
    elif hasattr(obj, "name") and hasattr(obj, "value"):
        # Handle other enum types generically
        return obj.name
    elif isinstance(obj, dict):
        return {key: _convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_convert_numpy_types(item) for item in obj)
    else:
        return obj


# GameMaster Tools
def initialize_poker_game(
    tool_context: ToolContext,
    initial_stacks: int = 100,
    small_blind: int = 1,
    big_blind: int = 2,
) -> Dict[str, Any]:
    """
    Initialize a new poker game with two players.

    Args:
        initial_stacks (int): Starting stack size for each player
        small_blind (int): Small blind amount
        big_blind (int): Big blind amount

    Returns:
        Dict containing game initialization status and initial state
    """
    global game_table, current_game_state

    try:
        # Create the poker table
        game_table = HoldemTable(
            initial_stacks=initial_stacks,
            small_blind=small_blind,
            big_blind=big_blind,
            render=False,
            funds_plot=False,
            max_raises_per_player_round=2,
            raise_illegal_moves=False,
        )

        # Add two dummy players (will be controlled by agents)
        class DummyAgent:
            def __init__(self, name):
                self.name = name

        game_table.add_player(DummyAgent("Player1"))
        game_table.add_player(DummyAgent("Player2"))

        # Reset and start the game
        game_table.reset()

        # Store initial state
        current_game_state = {
            "game_initialized": True,
            "num_players": 2,
            "initial_stacks": initial_stacks,
            "small_blind": small_blind,
            "big_blind": big_blind,
            "current_hand": 1,
        }

        # Store in session state
        tool_context.state["game_state"] = current_game_state
        tool_context.state["game_table_initialized"] = True

        log.info("Poker game initialized successfully")
        return {
            "status": "success",
            "message": "Poker game initialized with 2 players",
            "game_state": current_game_state,
        }

    except Exception as e:
        log.error(f"Failed to initialize poker game: {e}")
        return {"status": "error", "message": f"Failed to initialize game: {str(e)}"}


def get_game_state(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the current state of the poker game.

    Returns:
        Dict containing comprehensive game state information
    """
    global game_table

    if not game_table:
        return {"status": "error", "message": "Game not initialized"}

    try:
        # Get the current game environment
        game_table._get_environment()

        # Extract relevant information
        state = {
            "status": "success",
            "stage": game_table.stage.name if game_table.stage else "UNKNOWN",
            "community_cards": [str(card) for card in game_table.table_cards]
            if game_table.table_cards
            else [],
            "community_pot": _convert_numpy_types(game_table.community_pot),
            "current_round_pot": _convert_numpy_types(game_table.current_round_pot),
            "current_player_seat": _convert_numpy_types(game_table.current_player.seat)
            if game_table.current_player
            else None,
            "current_player_name": game_table.current_player.name
            if game_table.current_player
            else None,
            "players": [],
            "legal_actions": [action.name for action in game_table.legal_moves]
            if hasattr(game_table, "legal_moves")
            else [],
            "done": game_table.done,
            "winner": _convert_numpy_types(game_table.winner_ix)
            if hasattr(game_table, "winner_ix")
            else None,
            "min_call": _convert_numpy_types(getattr(game_table, "min_call", 0)),
            "dealer_position": _convert_numpy_types(game_table.dealer_pos),
        }

        # Add player information
        for i, player in enumerate(game_table.players):
            player_info = {
                "seat": _convert_numpy_types(player.seat),
                "name": player.name,
                "stack": _convert_numpy_types(player.stack),
                "cards": [str(card) for card in player.cards] if player.cards else [],
                "current_bet": _convert_numpy_types(game_table.player_pots[i])
                if i < len(game_table.player_pots)
                else 0,
                "is_active": _convert_numpy_types(
                    i < len(game_table.player_cycle.alive)
                    and game_table.player_cycle.alive[i]
                )
                if game_table.player_cycle
                else True,
            }
            state["players"].append(player_info)

        # Convert any remaining numpy types and update session state
        state = _convert_numpy_types(state)
        tool_context.state["current_game_state"] = state

        return state

    except Exception as e:
        log.error(f"Error getting game state: {e}")
        return {"status": "error", "message": f"Error getting game state: {str(e)}"}


def process_player_action(
    tool_context: ToolContext, action_name: str
) -> Dict[str, Any]:
    """
    Process a player's action in the poker game.

    Args:
        action_name (str): Name of the action to take (FOLD, CHECK, CALL, RAISE_3BB, etc.)

    Returns:
        Dict containing the result of the action
    """
    global game_table

    if not game_table:
        return {"status": "error", "message": "Game not initialized"}

    try:
        # Convert action name to Action enum
        action = Action[action_name.upper()]

        # Execute the action
        observation, reward, done, info = game_table.step(action.value)

        # Get updated game state
        updated_state = get_game_state(tool_context)

        result = {
            "status": "success",
            "action_taken": action_name,
            "reward": _convert_numpy_types(reward),
            "done": done,
            "game_state": updated_state,
            "info": _convert_numpy_types(info),
        }

        # Convert any remaining numpy types and update session state
        result = _convert_numpy_types(result)
        tool_context.state["last_action"] = result

        log.info(f"Processed action {action_name} for current player")
        return result

    except KeyError:
        return {
            "status": "error",
            "message": f"Invalid action: {action_name}. Valid actions are: {[action.name for action in Action]}",
        }
    except Exception as e:
        log.error(f"Error processing action {action_name}: {e}")
        return {"status": "error", "message": f"Error processing action: {str(e)}"}


def check_game_over(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Check if the game is over and determine the winner.

    Returns:
        Dict containing game over status and winner information
    """
    global game_table

    if not game_table:
        return {"status": "error", "message": "Game not initialized"}

    try:
        result = {
            "status": "success",
            "game_over": game_table.done,
            "winner": None,
            "final_stacks": [],
        }

        if game_table.done:
            # Find the winner (player with chips remaining)
            for i, player in enumerate(game_table.players):
                result["final_stacks"].append(
                    {
                        "player": player.name,
                        "seat": _convert_numpy_types(player.seat),
                        "final_stack": _convert_numpy_types(player.stack),
                    }
                )
                if player.stack > 0:
                    result["winner"] = {
                        "name": player.name,
                        "seat": _convert_numpy_types(player.seat),
                        "final_stack": _convert_numpy_types(player.stack),
                    }

        # Convert any remaining numpy types
        result = _convert_numpy_types(result)
        return result

    except Exception as e:
        log.error(f"Error checking game over: {e}")
        return {"status": "error", "message": f"Error checking game over: {str(e)}"}


# Player Tools
def get_player_hand(tool_context: ToolContext, player_seat: int) -> Dict[str, Any]:
    """
    Get a specific player's hand cards (private information).

    Args:
        player_seat (int): Seat number of the player (0 or 1)

    Returns:
        Dict containing the player's hand cards
    """
    global game_table

    if not game_table:
        return {"status": "error", "message": "Game not initialized"}

    try:
        if player_seat < 0 or player_seat >= len(game_table.players):
            return {"status": "error", "message": f"Invalid player seat: {player_seat}"}

        player = game_table.players[player_seat]

        result = {
            "status": "success",
            "player_name": player.name,
            "seat": _convert_numpy_types(player_seat),
            "hand_cards": [str(card) for card in player.cards] if player.cards else [],
            "stack": _convert_numpy_types(player.stack),
        }

        return _convert_numpy_types(result)

    except Exception as e:
        log.error(f"Error getting player hand for seat {player_seat}: {e}")
        return {"status": "error", "message": f"Error getting player hand: {str(e)}"}


def get_legal_actions(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the legal actions available to the current player.

    Returns:
        Dict containing legal actions and related information
    """
    global game_table

    if not game_table:
        return {"status": "error", "message": "Game not initialized"}

    try:
        game_table._get_legal_moves()

        result = {
            "status": "success",
            "legal_actions": [action.name for action in game_table.legal_moves],
            "current_player": game_table.current_player.name
            if game_table.current_player
            else None,
            "current_player_seat": _convert_numpy_types(game_table.current_player.seat)
            if game_table.current_player
            else None,
            "min_call": _convert_numpy_types(getattr(game_table, "min_call", 0)),
            "current_bet": _convert_numpy_types(
                game_table.player_pots[game_table.current_player.seat]
            )
            if game_table.current_player
            else 0,
        }

        return _convert_numpy_types(result)

    except Exception as e:
        log.error(f"Error getting legal actions: {e}")
        return {"status": "error", "message": f"Error getting legal actions: {str(e)}"}


def calculate_pot_odds(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Calculate pot odds for the current decision.

    Returns:
        Dict containing pot odds information
    """
    global game_table

    if not game_table:
        return {"status": "error", "message": "Game not initialized"}

    try:
        total_pot = game_table.community_pot + game_table.current_round_pot
        call_amount = getattr(game_table, "min_call", 0)

        if call_amount > 0:
            pot_odds = total_pot / call_amount
            pot_odds_percentage = call_amount / (total_pot + call_amount) * 100
        else:
            pot_odds = float("inf")
            pot_odds_percentage = 0

        result = {
            "status": "success",
            "total_pot": _convert_numpy_types(total_pot),
            "call_amount": _convert_numpy_types(call_amount),
            "pot_odds": _convert_numpy_types(pot_odds),
            "pot_odds_percentage": round(
                float(_convert_numpy_types(pot_odds_percentage)), 2
            ),
            "current_player": game_table.current_player.name
            if game_table.current_player
            else None,
        }

        return _convert_numpy_types(result)

    except Exception as e:
        log.error(f"Error calculating pot odds: {e}")
        return {"status": "error", "message": f"Error calculating pot odds: {str(e)}"}


def exit_game_loop(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Signal that the game loop should end (called when game is over).

    Returns:
        Dict containing exit status
    """
    log.info("Game loop exit requested")
    tool_context.actions.escalate = True

    return {"status": "success", "message": "Game loop terminated"}
