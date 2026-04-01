
  # Farming Icons — Resume Note
  _Written 2026-03-23 before system reset_
  
  ## What we were doing
  Generating a first-pass set of 13 farming game icons using Flux2 t2i.
  
  ## Art style spec
  - Soft vector illustration
  - Thick black ink outline
  - Pastel color fills
  - Rounded organic shapes
  - Pure white background
  - Flat shading with subtle cel highlights
  - Cozy / Luma Island style — NOT pixel art
  
  ## 13 subjects
  1. wheat seed
  2. carrot seed
  3. tomato seed
  4. wheat stalk
  5. carrot
  6. tomato
  7. green sprout
  8. watering can (full — water pouring from spout)
  9. watering can (empty — dry, tilted)
  10. water droplet
  11. coin (gold, wheat emblem)
  12. fertilizer/compost bag (burlap sack, leaf logo)
  
  (watering can full + empty = 2, total = 13 ✓)
  
  ## What still needs to be done
  Nothing was created yet. The plan was:
  
  ### Step 1 — Create square icon workflow
  Copy `batch/image_flux2_text_to_image.json` → `batch/farming_icons_t2i.json`
  Change two nodes:
  - `98:48` (Flux2Scheduler): width 1200→768, height 800→768
  - `98:47` (EmptyFlux2LatentImage): width 1200→768, height 800→768
  Also update filename_prefix in node `9` to `FarmIcon_`
  
  ### Step 2 — Create runs file
  Write `batch/farming_icons_runs.txt` — one prompt per line.
  
  Style anchor (prepend to every prompt):
  `single game icon, soft vector illustration, thick black ink outline, pastel color fills, rounded organic shapes, pure white background, centered composition, cozy farming game UI art, flat shading with subtle cel highlights, no drop shadow, no texture`
                                                                              
  Prompts (subject appended after em-dash):                                   
  ```                      
  <style anchor> — a single plump oval wheat seed, warm golden-yellow color, small nub at base
  <style anchor> — a tiny teardrop-shaped carrot seed, pale orange-brown, small root tip visible
  <style anchor> — a small flat oval tomato seed, pale cream color with faint reddish tint
  <style anchor> — a tall golden wheat stalk with a full drooping grain head and two small side leaves
  <style anchor> — a plump orange carrot with bright green feathery leafy top, slightly tapered root
  <style anchor> — a round red tomato with a bright green star cap and one small curling leaf
  <style anchor> — a tiny green seedling with two round cotyledon leaves emerging from a small dark soil mound
  <style anchor> — a blue watering can with water visible at the top opening, water droplets cascading from the rose spout
  <style anchor> — a pale grey watering can tilted sideways showing empty interior, small dust motes, dry cracked appearance
  <style anchor> — a single plump teardrop-shaped blue water droplet with a white highlight
  <style anchor> — a round gold coin with a small wheat sheaf emblem stamped on the face, glinting rim
  <style anchor> — a small brown burlap sack tied at the top with twine, green leaf logo on front, slightly bulging with granule contents
  ```                   
                                                                              
  Wait — that's only 12 prompts. The 13th subject seems to not be in the original list. Re-check with user on resume.
                                                                              
  ### Step 3 — Check ComfyUI is running
  `curl -s http://localhost:8188/system_stats | python3 -m json.tool`         
  If not running: `bash /home/derek/ComfyUI/start_comfyui.sh`
                                                                              
  ### Step 4 — Submit batch                     
  ```                                                                         
  python3 batch/batch_comfy.py batch/farming_icons_t2i.json batch/farming_icons_runs.txt --wait
  ```                                                                         
  Run with `run_in_background=true`.
                                                                              
  ## Output location                                         
  `/home/derek/ComfyUI/output/FarmIcon_*.png`
  
  ## After generation                                                         
  - View results                         
  - Note which subjects need a second pass
  - Check if style is consistent across the set
  - User may have found a free pack in the meantime — compare and decide which to use
