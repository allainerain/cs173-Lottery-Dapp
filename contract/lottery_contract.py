import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(5),
            max_tickets = sp.nat(5),
            ## uncomment below for deployment
            # admin = sp.address("tz1bzS3NznvMz6U7DcdUH6o7DJuGjnkXtTo6"),
            
            # uncomment below for testing
            admin = sp.test_account("admin").address,
            paid_amount = sp.tez(0),
        )
    
    #entry point to buy the tickets
    #modified to allow the user to buy multiple tickets at once
    @sp.entry_point
    def buy_ticket(self, ticket_amount):
        sp.set_type(ticket_amount, sp.TNat)
   
        # determining the amount that the user has to pay
        cost = sp.local('cost',sp.tez(0))
        sp.for i in sp.range(0, ticket_amount):
            cost.value = cost.value + sp.tez(1)
        self.data.paid_amount = cost.value
        
        # Sanity checks
        sp.verify(self.data.tickets_available >= ticket_amount, "NO TICKETS AVAILABLE")
        sp.verify(sp.amount >= cost.value, "INVALID AMOUNT")

        # Storage updates
        # adds the player to the map and updates the available tickets
        self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - ticket_amount)

        # Return extra tez balance to the sender
        extra_balance = sp.amount - cost.value
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    #entry point to end the game
    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        # takes the random number and gets the modulo of the random number with respect to the number of players
        divider = sp.len(self.data.players)
        winner_id = random_number % divider
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    #entry point to change the cost of the ticket
    @sp.entry_point
    def change_ticket_cost(self, new_cost):
        sp.set_type(new_cost, sp.TMutez)

        # Check if admin
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        # Check if the game has started
        sp.verify(sp.len(self.data.players) == 0, "GAME HAS STARTED")

        self.data.ticket_cost = new_cost

    #entry point to change the max amount of tickets
    @sp.entry_point
    def change_max_tickets(self, new_max):
        sp.set_type(new_max, sp.TNat)

        # Check if admin
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        # Check if the game has started
        sp.verify(sp.len(self.data.players) == 0, "GAME HAS STARTED")

        self.data.max_tickets = new_max
        self.data.tickets_available = new_max
        
    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")


#Tests
@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")
    john = sp.test_account("john")

    # Contract instance
    lottery = Lottery()
    scenario += lottery

    ## COMMENT OUT FOR DEPLOYMENT
    # change_max_tickets
    scenario.h2("change_max_tickets (valid test)")
    scenario += lottery.change_max_tickets(3).run(sender = admin)
    scenario += lottery.change_max_tickets(5).run(sender = admin)

    #change_max_tickets
    scenario.h2("change_max_tickets (failure test)")
    scenario += lottery.change_max_tickets(3).run(sender = alice, valid = False)

    ## COMMENT OUT FOR DEPLOYMENT
    #change_ticket_cost
    scenario.h2("change_ticket_cost (valid test)")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(sender = admin)
    scenario += lottery.change_ticket_cost(sp.tez(1)).run(sender = admin)

    scenario.h2("change_ticket_cost (failure test)")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(sender = alice, valid = False)

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(2), sender = bob)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(3), sender = john, valid = False) #trying to buy without enough tickets available
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(1), sender = charles, valid = False) #trying to buy without enough balance
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(2), sender = mike)

    scenario.h2("change_ticket_cost (failure test)")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(sender = admin, valid = False)

    ## COMMENT OUT FOR DEPLOYMENT
    #change_max_tickets
    scenario.h2("change_max_tickets (failure test)")
    scenario += lottery.change_max_tickets(5).run(sender = admin, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(2).run(sender = admin)