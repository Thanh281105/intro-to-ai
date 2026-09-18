# Competitive rules

Both agents observe the same pre-resolution state and choose independently. Actions are then resolved simultaneously. Same destination, direct swap, entering the opponent's cell, and conflicting pushes are blocked conservatively. Players never share a cell or pass through each other.

A box placed on a goal receives the pushing agent's ownership. Leaving a goal clears ownership; later completion may transfer ownership. The winner after exactly `n` steps is the agent with more currently owned boxes on goals; equal scores are a tie. This is the deterministic interpretation used by the executable implementation.
