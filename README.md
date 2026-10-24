# Chess & AI Coach — Minimalist Python Suite

> A single-file, zero-dependency **Chess Game & AI Coach** built with Python and Tkinter, featuring a strict **3-color palette**, Minimax AI with alpha-beta pruning, and optional **Gemini 3.8 Flash** analysis.

---

## ✦ Design Philosophy

Designed with strict visual constraints for a calm, distraction-free board game experience:
- **Deep Chocolate Brown** (`#3B2314`) — Board dark squares, typography, borders, and UI accents.
- **Soft Sage** (`#9CAF88`) — Active selection, legal move dots, and hint highlights.
- **Warm Cream** (`#F5EFE6`) — Board light squares, application canvas, and modal surfaces.

## ♟️ Key Features

- **Single-File Architecture:** The entire chess rules engine, Minimax search, Tkinter vector canvas, and AI coaching integration reside in a single self-contained [`main.py`](main.py).
- **Full Standard Chess Rules:**
  - En Passant, Castling (Kingside & Queenside), and Pawn Promotion.
  - Check, Checkmate, and Stalemate validation.
  - Move history snapshot stack with complete Undo support.
- **Built-in Minimax AI Engine:**
  - Evaluates piece values and positional Piece-Square Tables (PST).
  - Alpha-Beta pruning search tree for rapid, intelligent computer moves.
- **Dual Play Modes:**
  - **Player vs AI:** Test your skills against the built-in Minimax engine.
  - **2-Player Pass & Play:** Play locally on a shared screen with board flip toggle.
- **Gemini 3.8 Flash AI Coach:**
  - Press the **Coach Hint** button to query Google GenAI (`gemini-3.8-flash` via the Interactions API) for strategic positional evaluation and grandmaster commentary.
  - Automatic graceful fallback to local heuristic analysis when offline or without an API key.

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+ (Tkinter included in standard Python distributions)
- *(Optional)* `google-genai` for Gemini AI Coach features

### Installation & Run

1. Clone the repository:
   ```bash
   git clone https://github.com/ZengLLQ/chess.git
   cd chess
   ```

2. *(Optional)* Install Google GenAI SDK and configure API key:
   ```bash
   pip install google-genai
   export GEMINI_API_KEY="your_api_key_here"  # Windows PowerShell: $env:GEMINI_API_KEY="your_key"
   ```

3. Launch the game:
   ```bash
   python main.py
   ```

## 🎮 Controls & Interface

- **Left-Click:** Select piece and move to valid highlighted square.
- **Mode Toggle:** Switch between "vs AI" and "2-Player" mode.
- **Flip Board:** Invert perspective between White and Black.
- **Undo:** Rewind moves step-by-step.
- **Coach Hint:** Request AI strategic advice on current board state.

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
