import hashlib
import json
from textwrap import dedent

from time import time
from uuid import uuid4

from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        #create the genesis block with its proof
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        creates and adds new block to chain
        proof: <int> proof given by proof of work algorithm
        previous_hash: <str> hash of previous block
        return value: <dict> new block


        each block has an index, timestamp, list of transactions, a proof
        and hash of previous block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        #reset current_transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        creates and adds new transaction to current_transactions
        sender: <str> address of sender
        recipient: <str> address of recipient
        amount: <int> amount
        return value: <int> index of block that holds transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        """
        Simple proof of work algorithm:
        -find number p' such that hash(pp') contains 4 leading zeros, where p is
            previous proof, and p' is new proof

        last_proof: <int>
        return value: <int>
        """

        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a block

        block: <dict> block
        return value: <str> hashed block
        """

        #must ensure dictionary is ordered or we'll have inconsisten hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof: does hash(last_proof, proof) contain 4 leading zeros?

        last_proof: <int> previous proof
        proof: <int> current proof
        return value: <bool>
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    @property
    def last_block(self):
        #returns last block in chain
        return self.chain[-1]

#instantiate our node
app = Flask(__name__)

#generate globally unique address for this node
node_identifier = str(uuid4()).replace('-','')

#instantiate the blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    #we run proof of work algorithm to get next proof
    last_block = blockchain.last_block
    last_proof =last_block['proof']
    proof =blockchain.proof_of_work(last_proof)

    #we must receive a reward for finding proof
    #sender is "0" to signify that this node has mined a new coin
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    #forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New block forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #check kthat required fields are in POST'ed data
    required =['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    #create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amoutn'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
