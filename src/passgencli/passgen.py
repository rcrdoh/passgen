import hashlib
import hmac
import base64
import json
import os
import sys
import sqlite3
from getpass import getpass
from pathlib import Path

DB_PATH = Path.home() / ".local/share/passgencli/db.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class ImprovedMentalSeedGenerator:
    """
    Mental seed password generator with hashed seeds
    
    Supports multiple hashing strategies:
    - simple: sha256(seed)
    - hmac: HMAC-SHA256(reference, seed)
    - pbkdf2: PBKDF2-HMAC-SHA256(seed, iterations)
    """
    
    def __init__(self, file_hint_name='passgen_hints.json', db_path = DB_PATH):
        self.CURRENT_PATH = os.getcwd()
        self.hint_file = os.path.expanduser(self.CURRENT_PATH+'/'+file_hint_name)
        self.db_path = db_path
        self.hints = self._load_hints()
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            reference TEXT,
            hash_method TEXT,
            iterations INTEGER,
            prev TEXT,
            seed_indices TEXT
        )
        """)
        conn.commit()
        conn.close()
        return 

    def _load_hints(self):

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT name, reference, hash_method, iterations, prev, seed_indices
            FROM registry
        """)

        result = {}

        for row in cur.fetchall():
            name, reference, hash_method, iterations, prev, seed_indices = row

            result[name] = {
                "seed_indices": json.loads(seed_indices) if seed_indices else [],
                "reference": reference,
                "hash_method": hash_method,
                "iterations": iterations,
                "prev": prev
            }

            if (result[name]['prev'] is None) or (result[name]['prev'] == ''):
                del result[name]['prev']

        conn.close()
        return result
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO registry (name, data)
            VALUES (?, ?)
        """, (name, json.dumps(data_dict)))

        conn.commit()
        conn.close()

    def __flatten_entry(self, name, data):
        return {
            "name": name,
            "reference": data.get("reference"),
            "hash_method": data.get("hash_method"),
            "iterations": data.get("iterations"),
            "prev": data.get("prev"),
            "seed_indices": json.dumps(data.get("seed_indices", []))
        }

    def _save_hints(self,name, data_dict):
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        flat_entry = self.__flatten_entry(name, data_dict)

        cur.execute("""
            INSERT OR REPLACE INTO registry
            (name, reference, hash_method, iterations, prev, seed_indices)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            flat_entry["name"],
            flat_entry["reference"],
            flat_entry["hash_method"],
            flat_entry["iterations"],
            flat_entry["prev"],
            flat_entry["seed_indices"]
        ))

        conn.commit()
        conn.close()
        return 
    
    def _delete_hints(self,name):
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("DELETE FROM registry WHERE name = ?", (name,))

        conn.commit()
        conn.close()
        return 
    
    def _hash_seed_simple(self, seed):
        """Simple SHA-256 hash of seed"""
        return hashlib.sha256(seed.encode()).hexdigest()
    
    def _hash_seed_hmac(self, seed, reference):
        """HMAC-based seed hashing with reference as key"""
        return hmac.new(
            reference.encode(),
            seed.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _hash_seed_pbkdf2(self, seed, reference, seed_index, iterations=50000):
        """PBKDF2-based seed hashing (expensive, secure)"""
        # Use reference + seed position as salt
        salt = f"{reference}_s{seed_index}".encode()
        
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            seed.encode(),
            salt,
            iterations
        )
        return hashed.hex()
    
    def generate_password(self, seeds, reference, 
                         hash_method='pbkdf2', iterations=10000, 
                         length=18):
        """
        Generate password from hashed seeds
        
        Args:
            seeds: List of seed words (from user's memory)
            reference: Site/service reference
            hash_method: 'simple', 'hmac', or 'pbkdf2'
            iterations: For PBKDF2 (default: 10000)
            length: Password length
        
        Returns:
            Generated password string
        """
        # Step 1: Hash each seed
        hashed_seeds = []
        for i, seed in enumerate(seeds):
            if hash_method == 'simple':
                hashed = self._hash_seed_simple(seed)
            elif hash_method == 'hmac':
                hashed = self._hash_seed_hmac(seed, reference)
            elif hash_method == 'pbkdf2':
                hashed = self._hash_seed_pbkdf2(seed, reference, i, iterations)
            else:
                raise ValueError(f"Unknown hash method: {hash_method}")
            
            hashed_seeds.append(hashed)
        
        # Step 2: Combine hashed seeds + reference
        combined = ''.join(hashed_seeds) + reference
        
        # Step 3: Final hash for password generation
        final_hash = hashlib.sha256(combined.encode()).digest()
        
        # Step 4: Convert to password format
        password = base64.urlsafe_b64encode(final_hash).decode()[:length]
        
        # Step 5: Ensure character diversity
        password = self._ensure_diversity(password)
        
        return password
    
    def _ensure_diversity(self, password):
        """Ensure password has required character types"""
        chars = list(password)
        
        # Ensure uppercase
        if not any(c.isupper() for c in chars):
            for i, c in enumerate(chars):
                if c.isalpha():
                    chars[i] = c.upper()
                    break
            else:
                chars[0] = 'A'
        
        # Ensure lowercase
        if not any(c.islower() for c in chars):
            for i, c in enumerate(chars):
                if c.isalpha() and c.isupper():
                    chars[i] = c.lower()
                    break
            else:
                chars[1] = 'a'
        
        # Ensure digit
        if not any(c.isdigit() for c in chars):
            chars[-1] = '7'
        
        # Ensure symbol
        symbols = '!@#$%^&*-_=+'
        if not any(c in symbols for c in chars):
            chars[-2] = '@'
        
        return ''.join(chars)
    
    def create_password(self, service):
        """Interactive password creation with hints"""
        print(f"\n=== Create password for: {service} ===\n")
        
        # Get recipe parameters
        seed_indices = input("Which seed numbers? (e.g., 1,3,5): ").strip()
        seed_indices = [int(x.strip()) for x in seed_indices.split(',')]
        
        reference = input("Reference (e.g., amz2024): ").strip()
        
        print("\nHash method:")
        print("  1. Simple (fast, good)")
        print("  2. HMAC (fast, better)")
        print("  3. PBKDF2 (slow, best) [recommended]")
        method_choice = input("Choice [3]: ").strip() or '3'
        
        hash_method_map = {
            '1': 'simple',
            '2': 'hmac',
            '3': 'pbkdf2'
        }
        hash_method = hash_method_map.get(method_choice, 'pbkdf2')
        
        iterations = 10000
        if hash_method == 'pbkdf2':
            iter_input = input("PBKDF2 iterations [10000]: ").strip()
            if iter_input:
                iterations = int(iter_input)
        
        # Get actual seeds (not stored!)
        print("\nEnter seed values (NOT stored):")
        seeds = []
        try:
            for idx in seed_indices:
                seed = getpass(f"Seed {idx}: ")
                seed_confirm = getpass(f"Seed confirm{idx}: ")
                assert seed == seed_confirm, "Seed confirmation have to be the same as original"
                seeds.append(seed)    
            
        except AssertionError:
            print("Seed confirmation have to be the same as original")
            sys.exit(1)
                
        
        # Generate password
        print("\nGenerating password...")
        password = self.generate_password(
            seeds, reference, hash_method, iterations
        )
        
        print(f"\n✓ Generated password: {password}")
        
        # Copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(password)
            print("✓ Copied to clipboard")
        except ImportError:
            print("(Install pyperclip for clipboard support)")
        
        # Save hint
        save = input("\nSave hint? [y/n]: ").strip().lower()
        if save == 'y':
            self.hints[service] = {
                'seed_indices': seed_indices,
                'reference': reference,
                'hash_method': hash_method,
                'iterations': iterations if hash_method == 'pbkdf2' else None
            }
            self._save_hints()
            print("✓ Hint saved")
    
    def get_password(self, service):
        """Retrieve password using saved hint"""
        if service not in self.hints:
            print(f"No hint found for: {service}")
            return
        
        hint = self.hints[service]
        print(f"\n=== Generate password for: {service} ===\n")
        print(f"Seeds: {hint['seed_indices']}")
        print(f"Reference: {hint['reference']}")
        print(f"Method: {hint['hash_method']}")
        if hint.get('iterations'):
            print(f"Iterations: {hint['iterations']}")
        print()
        
        # Get seeds from user
        print("Enter seed values:")
        seeds = []
        for idx in hint['seed_indices']:
            seed = getpass(f"Seed {idx}: ")
            seeds.append(seed)
        
        # Generate
        print("\nGenerating password...")
        password = self.generate_password(
            seeds,
            hint['reference'],
            hint['hash_method'],
            hint.get('iterations', 10000)
        )
        
        print(f"\n✓ Generated password: {password}")
        
        # Copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(password)
            print("✓ Copied to clipboard")
            
            # Auto-clear after 30s
            import threading
            def clear():
                import time
                time.sleep(30)
                pyperclip.copy('')
                print("\n✓ Clipboard cleared")
            threading.Thread(target=clear, daemon=True).start()
        except ImportError:
            pass
    
    def list_services(self):
        """List all saved hints"""
        if not self.hints:
            print("No hints saved")
            return
        
        print("\n=== Saved Hints ===\n")
        for service, hint in sorted(self.hints.items()):
            print(f"{service}:")
            print(f"  Seeds: {hint['seed_indices']}")
            print(f"  Reference: {hint['reference']}")
            print(f"  Method: {hint['hash_method']}")
            if hint.get('iterations'):
                print(f"  Iterations: {hint['iterations']}")
            print()


# CLI interface
def main():
    import sys
    
    gen = ImprovedMentalSeedGenerator()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  passgen.py create <service>")
        print("  passgen.py get <service>")
        print("  passgen.py list")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create': 
        service = sys.argv[2] if len(sys.argv) > 2 else input("Service: ")
        gen.create_password(service)
    
    elif command == 'get':
        service = sys.argv[2] if len(sys.argv) > 2 else input("Service: ")
        gen.get_password(service)
    
    elif command == 'list':
        gen.list_services()
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
