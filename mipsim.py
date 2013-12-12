#!/usr/bin/env python
#===============================================================================
#    HOWARD GRIMBERG
#    MIPS PIPELINE SIMULATOR PROJECT
#    EECS 643 - Fall 2013
#    Licensed under the MIT License
#    Copyright 2013- Howard Grimberg
#===============================================================================


# Instruction class to contain information about a single instruction.
class instruction():
    iOp = 'DADD'
    iLabel = None
    iOffset = 0
    rd = 0
    rs = 0
    rt = 0

    # Similar to Object.toString() in Java, overrides the string pring
    # for debug purposes.
    def __str__(self):
        return '%s    %s %s,%s,%s' % (self.iLabel, self.iOp, self.rd, self.rs, self.rt)



# Parse accepts a file object and returns two dictionaries and a list
# that contain Register File, Memory and Instructions (all at once)
def parse(inputfile):
    # Declare a few dictionaries for memory and registers
    mem = {}
    regs = {}

    # List for instructions
    insts = []

    new_pc = -1

    # Set memory and registers to 0
    for i in range (0, 32):
        regs[str(i)] = 0
    for i in range(0, 1000, 8):
        mem[str(i)] = 0

    # Start by assuming we are reader registers
    state = 'r';

    # Read file one line at a time
    for line in inputfile:
        line = line.strip()

        # Determine what part of the input file we are reading and  set the state
        if line == "" or line.isspace():
            pass
        elif line == "REGISTERS":
            state = 'r'
        elif line == 'MEMORY':
            state = 'm'
        elif line == 'CODE':
            state = 'c'
        else:
            # Depending what state we are in,
            # process the text file appropriately
            if state == 'r':
                # Remove extra whitespace from the line
                line = line.strip()

                # Split on space
                rs = line.split()

                # First entry in array(from) slit, everything
                # past the first character is a reg. number
                rn = rs[0][1:]
                val = rs[1]
                regs[rn] = val
            elif state == 'm':

                # Same basic idea for memory
                line = line.strip()
                ms = line.split()
                mn = ms[0]
                mv = ms[1]
                mem[mn] = mv
            elif state == 'c':

                # Make an  empty instruction
                nIns = instruction()

                # Does it have a label?
                if line.find(':') > -1:
                    #Grab the label and put it in the instruction
                    sp = line.split(':')
                    # Remove the label, clean the line and put it back
                    # for further processing (as normal)
                    line = sp[1].strip()
                    nIns.iLabel = sp[0].strip()
                else:
                    pass
                # Branch Parsing
                if line.find('BNEZ') > -1:
                    line = line.strip()
                    ppre = line.split(' ', 1)
                    rds = [x.strip() for x in ppre[1].split(',')]
                    nIns.rd = rds[0][1:]
                    nIns.iOp = 'BNEZ'
                    nIns.rs = rds[1][0:]
                    nIns.iType = 'b'
                elif line.find('#') > -1:
                    line = line.strip()
                    ins = line.split(' ', 1)
                    nIns.iOp = ins[0].strip()
                    rds = [x.strip() for x in ins[1].split(',')]
                    nIns.rd = rds[0][1:]
                    nIns.rs = rds[1][1:]
                    nIns.rt = rds[2][1:]
                    nIns.iType = 'i'
                elif line.find('(') > -1:
                    line = line.strip()
                    ins = line.split(' ', 1)
                    nIns.iOp = ins[0].strip()
                    rds = [x.strip() for x in ins[1].split(',')]



                    l = rds[1].find('(')
                    r = rds[1].find(')')

                    if(nIns.iOp == 'SD'):
                        nIns.rd = rds[1][l + 1:r][1:]
                        nIns.rs = rds[0][1:]
                    elif(nIns.iOp == 'LD'):

                        nIns.rs = rds[1][l + 1:r][1:]
                        nIns.rd = rds[0][1:]
                    else:
                        pass

                    l = rds[1].find('(')

                    nIns.iOffset = rds[1][:l]

                    nIns.iType = 'm'
                else:
                    line = line.strip()
                    ins = line.split(' ', 1)
                    nIns.iOp = ins[0].strip()
                    rds = [x.strip() for x in  ins[1].split(',')]

                    nIns.rd = rds[0][1:]
                    nIns.rs = rds[1][1:]
                    nIns.rt = rds[2][1:]
                    nIns.iType = 'r'
                insts.append(nIns)

    return mem, regs, insts


# Ask user for information
def inquire_user():

    in_file = raw_input('Enter an input file name: ')
    out_file = raw_input('Enter an output file name: ')

    return in_file, out_file


# Given instructions in memory stages 1 and 2 and a register
# check if there may be a hazard
def  stalled(rn, mem1, mem2):
    if(mem1):
        if (mem1.iOp == 'LD' and mem1.rd == rn):
            return True
    if(mem2):
        if(mem2.iOp == 'LD' and mem2.rd == rn):
            return True

    return False


# Given reigsters, instructions and memory, return
# registers, memory and a string of pipeline state.
def do_sim(mem, regs, ins):

    # Set The Clock  To Start At 1

    clock = 1
    pc = 0
    returnable = ""

    # Set all pipeline registers to None, indicating they are empty.
    ifs1 = None
    ifs2 = None
    ids = None
    exs = None
    mem1 = None
    mem2 = None
    mem3 = None
    delay_ins = None
    wb = None
    done = False

    # Bypass is used to indicate if a branch has occured
    bypass = False

    # Set pc at -1 as the first instruction is at location 0
    # in the instruction list.
    new_pc = -1

    # Sett the stall counter to 0
    stall = 0

    # No, we have not started
    started = False

    # Set interstatial counts, with IF1 being 1 since the first
    # instruction is #1 (for our purposes). The other stages have no
    # meaning and are set to 0.
    counter = {'ifs1':1, 'ifs2':0, 'ids':0, 'exs':0, 'mem1':0, 'mem2':0, 'mem3':0, 'wb':0}

    # Prepare a dictionary of labels and the corresponding PC for that label
    label_map = {}
    for idx, i in enumerate(ins):
        if i.iType != 'b' and i.iLabel != None:
            label_map[str(i.iLabel)] = idx
        else:
            pass


    #===========================================================================
    #     SYNTAX NOTE
    #     Flushing happens when the stage in questions is set to None
    #     If the stage contains nothing, the If statement will fail
    #
    #     if(some_stage):
    #        print 'Something Here"
    #===========================================================================



    #===============================================================================
    #     Keep runing until there is either nothing in the pipeline or started is False
    #     Use the started variable to artifically force the loop.
    #
    #     Python has no concept of a 'for' loop, only a foreach loop.
    #     as such it is very difficult to complete without knowing the final instruction count
    #===============================================================================

    while wb is not None or mem1 is not None or mem2 is not None or mem3 is not None or exs is not None or ids is not None or ifs2 is not None or ifs1 is not None or not started:
        started = True

        # Append our clock

        returnable = returnable + 'c#' + str(clock) + ' '

        # WB Stage
        if (wb):
            returnable = returnable + 'I' + str(counter['wb']) + '-WB '

        # MEM3
        if(mem3):

            returnable = returnable + 'I' + str(counter['mem3']) + '-MEM3 '

        # MEM2 Stage
        if(mem2):
            # Handle SD Instruction
            if mem2.iOp == 'SD':
                # Calculate the intended memory address
                final_mem = str(int(regs[str(mem2.rd)]) + int(mem2.iOffset))

                # Put the register in the intended address
                mem[str(final_mem)] = regs[str(mem2.rs)]

            # Handle LD Instruction
            elif mem2.iOp == 'LD':
                # Calculate intended (Read) address
                final_mem = str(int(regs[str(mem2.rs)]) + int(mem2.iOffset))

                # Perform the read
                regs[str(mem2.rd)] = mem[final_mem]


            returnable = returnable + 'I' + str(counter['mem2']) + '-MEM2 '

        # MEM1 Stage
        if(mem1):
            returnable = returnable + 'I' + str(counter['mem1']) + '-MEM1 '


        # EX Stage
        if(exs):
            stall = 0
            if(stalled(exs.rt, mem1, mem2) and stalled(exs.rs, mem1, mem2) and False):
                stall = 1

            else:
                # Check the instruction operand
                if exs.iOp == 'DADD':

                    # Check for a stall in case of cascading stalls.
                    if(stalled(exs.rt, mem1, mem2) or stalled(exs.rs, mem1, mem2)):
                        stall = 1
                    else:
                        # Check what the instruction type is
                        if exs.iType == 'r':
                            regs[str(exs.rd)] = int(regs[exs.rs]) + int(regs[exs.rt])
                        # Immediate Instruction ? Why yes it is!
                        elif exs.iType == 'i':
                            regs[str(exs.rd)] = int(regs[exs.rs]) + int(exs.rt)

                # Same as DADD only fo SUB
                elif  exs.iOp == 'SUB':
                    if(stalled(exs.rt, mem1, mem2) or stalled(exs.rs, mem1, mem2)):
                        stall = 1
                    else:
                        if exs.iType == 'r':
                            regs[str(exs.rd)] = int(regs[exs.rs]) - int(regs[exs.rt])
                        elif exs.iType == 'i':
                            regs[str(exs.rd)] = int(regs[exs.rs]) - int(exs.rt)

                # Handle the branch case (very messy)
                elif exs.iOp == 'BNEZ':
                    if(stalled(exs.rt, mem1, mem2) or stalled(exs.rs, mem1, mem2)):
                        stall = 1
                    else:

                        rs_num = int(regs[str(exs.rd)])
                        if (rs_num != 0):

                            # Find New PC
                            new_pc = label_map[str(exs.rs)]
                            # Set PC
                            pc = new_pc

                            # FLUSH EVERYTHING!!
                            bypass = True
                        else:
                            pass

                # Check if there is still something to talk about
                if(exs):
                    # Check for a stall
                    if (stall > 0):
                        returnable = returnable + 'I' + str(counter['exs']) + '-stall '
                        pass
                    else:
                        # Behave as normal
                        returnable = returnable + 'I' + str(counter['exs']) + '-EX '


        # Decode Stage
        if(ids):
            # Check for stall
            if(stall > 0):
                returnable = returnable + 'I' + str(counter['ids']) + '-stall '

            # No stall, then has a branch happened.
            # If this has happened, the NEXT instruction will flushed.
            # Print the instruction THEN flush it.

            elif(bypass):
                returnable = returnable + 'I' + str(counter['ids']) + '-ID '
                ids = None
            else:
                returnable = returnable + 'I' + str(counter['ids']) + '-ID '

        # Fetch 2 Stage

        # Check if there is something in IF2
        if(ifs2):

            if(stall > 0):
                returnable = returnable + 'I' + str(counter['ifs2']) + '-stall '
            elif(bypass):
                returnable = returnable + 'I' + str(counter['ifs2']) + '-IF2 '
                ifs2 = None
            else:
                returnable = returnable + 'I' + str(counter['ifs2']) + '-IF2 '



        # IF1 stage begins here. We DO NOT check if its empty since that would block furhter execution
        # THe IF1 stage is supposed to be loading the instruction from the PC
        if(stall > 0):

            # Safety check if there is still something to print
            if(ifs1 is None):
                if(pc < len(ins)):
                    returnable = returnable + 'I' + str(counter['ifs1']) + '-stall '

        # If we are ina bypass
        elif(bypass):

            # FLush IFS1
            ifs1 = None

            # bypass = False
            # I don't think this is doing anything. This is a leftover that I am afraid to remove
            #
            if(ifs1):
                returnable = returnable + 'I' + str(counter['ifs1']) + '-IF1 '

                # bypass = False
                new_pc = -1
        else:
            if(len(ins) > pc):
                ifs1 = ins[pc]
                returnable = returnable + 'I' + str(counter['ifs1']) + '-IF1 '
                pc = pc + 1

            else:
                ifs1 = None

        # Instructions/Counters are advanced
        wb = mem3
        counter['wb'] = counter['mem3']
        mem3 = mem2
        counter['mem3'] = counter['mem2']
        mem2 = mem1
        counter['mem2'] = counter['mem1']
        mem1 = None

        # Don't advance anything beyond MEM1 if there is a stall
        if(stall == 0):
            mem1 = exs
            counter['mem1'] = counter['exs']
            exs = ids
            counter['exs'] = counter['ids']
            ids = ifs2
            counter['ids'] = counter['ifs2']
            ifs2 = ifs1
            counter['ifs2'] = counter['ifs1']

        # Only advance PC if there IS NO stall and NO BRANCH
        if(stall > 0):
            pass
        elif(bypass):
               bypass = False
        elif(stall == 0):
            # Only increment PC if there is no stall(or really causing a stall upong signal from the EX unit)
            counter['ifs1'] = counter['ifs1'] + 1

        # Add newline
        returnable = returnable + '\n'

        # Increment Clock
        clock = clock + 1

    # Return everything
    return returnable, regs, mem

# Main Function. Separated like this so I can debug it in the
# python shell.
def __entry():
    print 'MIPSIM PROJECT'
    print 'Copyright 2013 - Howard Grimberg'
    print 'Licensed under the MIT License'
    print 'See LICENSE.txt for Details\n'
    print 'INTERACTIVE MODE'

    # Loop flag for request
    done = False

    while not done:
        inf, outf = inquire_user()
        try:
            finf = open(inf, 'r')
        except:
            print 'Bad Input File. Exiting...'
            break

        mem, regs, ins = parse(finf)
        finf.close()

        res, regs2, mem2 = do_sim(mem, regs, ins)
        f = open(outf, 'w')

        f.write(res + '\n')

        f.write("REGISTERS\n")

        ksr = [int(x) for x in  regs2.iterkeys() ]
        for key in sorted(ksr):
            if(regs2[str(key)] != 0):
                f.write("R%s %s \n" % (key, str(regs2[str(key)])))
        ksm = [int(x) for x in  mem2.iterkeys() ]


        f.write("MEMORY\n")
        for key in sorted(ksm):
            if(mem2[str(key)] != 0):
                f.write("%s %s \n" % (key, str(mem2[str(key)])))

        f.close()

        exit = raw_input('Exit? (y/n) [n]: ')
        if(exit.lower() == 'y'):
            done = True


if __name__ == "__main__":
    __entry();




