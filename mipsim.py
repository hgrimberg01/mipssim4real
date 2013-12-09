#!/usr/bin/env python
class instruction():
    iOp='DADD'
    iLabel=None
    iOffset = 0
    rd = 0
    rs = 0
    rt = 0
    def __str__(self):
        return '%s    %s %s,%s,%s' % (self.iLabel,self.iOp,self.rd,self.rs,self.rt)




def parse(inputfile):
    mem = {}
    regs = {}
    new_pc = -1
    for i in range (0,32):
        regs[str(i)] = 0
    for i in range(0,1000,8):
        mem[str(i)] = 0

    insts =  []
    state = 'r';
    for line in inputfile:
        line = line.strip()
        if line == "\n":
            state = 'empty'
        elif line == "REGISTERS":
            state = 'r'
        elif line == 'MEMORY':
            state = 'm'
        elif line == 'CODE':
            state = 'c'
        else:
            if state == 'r':
                line = line.strip()
                rs = line.split()
                rn = rs[0][1:]
                val =  rs[1]
                regs[rn] = val
            elif state == 'm':
                line = line.strip()
                ms = line.split()
                mn = ms[0]
                mv = ms[1]
                mem[mn] = mv
            elif state == 'c':
                nIns = instruction()
                if line.find(':') > -1:
                    sp = line.split(':')
                    line = sp[1].strip()
                    nIns.iLabel = sp[0].strip()
                else:
                    pass

                if line.find('BNEZ') > -1:
                    line = line.strip()
                    ppre = line.split(' ',1)
                    rds =  [x.strip() for x in ppre[1].split(',')]
                    nIns.rd = rds[0][1:]
                    nIns.iOp = 'BNEZ'
                    nIns.rs = rds[1][0:]
                    nIns.iType = 'b'
                elif line.find('#') > -1:
                    line = line.strip()
                    ins = line.split(' ',1)
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
                    rgx = '/\(([^)]+)\)/'


                    l= rds[1].find('(')
                    r =rds[1].find(')')

                    if(nIns.iOp == 'SD'):
                        nIns.rd = rds[1][l+1:r][1:]
                        nIns.rs =  rds[0][1:]
                    elif(nIns.iOp == 'LD'):

                        nIns.rs = rds[1][l+1:r][1:]
                        nIns.rd = rds[0][1:]
                    else:
                        pass

                    l= rds[1].find('(')

                    nIns.iOffset =  rds[1][:l]

                    nIns.iType = 'm'
                else:
                    line = line.strip()
                    ins = line.split(' ',1)
                    nIns.iOp = ins[0].strip()
                    rds =[x.strip() for x in  ins[1].split(',')]

                    nIns.rd = rds[0][1:]
                    nIns.rs = rds[1][1:]
                    nIns.rt = rds[2][1:]
                    nIns.iType = 'r'
                insts.append(nIns)

    return mem,regs,insts



def inquire_user():


    return in_file, out_file


def  stalled(rn, mem1, mem2):
    if(mem1):
        if (mem1.iOp == 'LD' and mem1.rd == rn):
            return True
    if(mem2):
        if( mem2.iOp == 'LD' and mem2.rd ==rn ):
            return True

    return False



def do_sim(mem,regs,ins):
    clock = 1
    pc = 0
    returnable = ""
    ifs1 = None
    ifs2 = None
    ids  = None
    exs  = None
    mem1 = None
    mem2 = None
    mem3 = None
    wb =  None
    done = False
    bypass = False
    new_pc = -1
    stall = 0
    label_map = {}
    
    #stalin = ('ex':0,'id':0,'ifs2':0, 'ifs1':0)

    for idx, i in enumerate(ins):
        if i.iType != 'b' and i.iLabel != None:
            label_map[str(i.iLabel)] = idx
        else:
            pass


    ifs1= ins[0]

    while wb is not None or mem1 is not None or mem2 is not None or mem3 is not None or exs is not None or ids is not None or ifs2 is not None or ifs1 is not None:
        returnable  =  returnable + 'c#'+ str(clock)+' '

        """ Writeback Stage """
        if (wb):
            returnable = returnable + 'I' + str(ins.index(wb)+1) + '-WB '

        """ Mem3 Stage """
        if(mem3):

            returnable = returnable + 'I' + str(ins.index(mem3)+1) + '-MEM3 '
        """ Mem2 Stage """
        if(mem2):

            if mem2.iOp == 'SD':
                final_mem =  str(int(regs[str(mem2.rd)]) +int( mem2.iOffset))
                mem[str(final_mem)] =   regs[str(mem2.rs)]
            elif mem2.iOp == 'LD':
                final_mem = str(int(regs[str(mem2.rs)]) +int( mem2.iOffset))

                regs[str(mem2.rd)] = mem[final_mem]
            
            
            returnable = returnable + 'I' + str(ins.index(mem2)+1) + '-MEM2 '

        """ Mem1 Stage """
        if(mem1):
            if(stall == 0):
                returnable = returnable + 'I' + str(ins.index(mem1)+1) + '-MEM1 '

          
        """ Exec Stage """
        if(exs):
            stall = 0
            if(stalled(exs.rt,mem1,mem2) and stalled(exs.rs,mem1,mem2) and False):
                stall =  1
                
            else:
                if exs.iOp == 'DADD':
                    if(stalled(exs.rt,mem1,mem2) or stalled(exs.rs,mem1,mem2)):
                        stall =  1
                    if exs.iType == 'r':
                        regs[str(exs.rd)] =   int(regs[exs.rs])+int(regs[exs.rt])
                    elif exs.iType =='i':

                        regs[str(exs.rd)] =   int(regs[exs.rs])+int(exs.rt)
                elif  exs.iOp == 'SUB':
                    if exs.iType == 'r':
                        regs[str(exs.rd)] =   int(regs[exs.rs]) - int(regs[exs.rt])
                    elif exs.iType =='i':

                        regs[str(exs.rd)] =   int(regs[exs.rs]) - int(exs.rt)
                elif exs.iOp == 'BNEZ':
                    if(stalled(exs.rt,mem1,mem2) or stalled(exs.rs,mem1,mem2)):
                        stall =  1
                    rs_num = int(regs[str(exs.rd)])
                    if (rs_num != 0):

                        #Handle Branch
                        new_pc =  label_map[str(exs.rs)]
                        #Flush Pipeline
                        ids = None
                        ifs2 = None
                        ifs1 = None
                        #Set pc to new pc
                        pc = new_pc
                        bypass =True
                        
                   
                    else:
                        bypass = False
                
                if(exs):
                    if (stall > 0):
                        returnable = returnable + 'I'+str(ins.index(exs)+1) + '-stall '
                        pass
                    else:
                        returnable = returnable + 'I' +str(ins.index(exs)+1) + '-EX '


        """ Decode Stage """
        if(ids):
            if(stall > 0):
                returnable = returnable + 'I'+ str(ins.index(ids)+1) + '-stall '
                pass
            else:
                returnable = returnable + 'I' + str(ins.index(ids)+1) + '-ID '

        """ Fetch2 Stage """
   
        if(ifs2):
            
            if(stall > 0):
                returnable = returnable + 'I'+str(ins.index(ifs2)+1) + '-stall '
            
            else:
                returnable = returnable + 'I' + str(ins.index(ifs2)+1) + '-IF2 '
       
      
        
        if(pc < len(ins)):
            ifs1 = ins[pc]
        
         
            new_pc = -1
   
        else:
            ifs1 = None
            
     
            
        if(stall == 0):

            pc = pc + 1 
           
            
  
        
        if(ifs1 != None):
            if(stall > 0):  
                returnable = returnable + 'I' + str(ins.index(ifs1)+1) + '-stall '
                
            else:
                returnable = returnable + 'I' + str(ins.index(ifs1)+1) + '-IF1 '
        else:
            pass     
        




        """ Stall checks and insertion of them """


   
        wb   = mem3
        mem3 = mem2
        mem2 = mem1
        
        mem1 = None
        
        if(stall == 0):
            mem1 = exs
           
            exs  = ids
            ids  = ifs2
            ifs2 = ifs1

        #stall = 0
        returnable =  returnable + '\n'
        clock = clock +1
        bypass = False
    return returnable,regs,mem


def main():
    f = open('input.txt','r')
    mem,regs,ins = parse(f)

    res,regs2,mem2= do_sim(mem,regs,ins)

    print res

    for key in sorted(regs2.iterkeys()):
        if(regs2[key] != 0):
            print "R%s %s" % (key,str( regs2[key]))

    print "MEMORY"
    for key in sorted(mem2.iterkeys()):
        if(mem2[key] != 0):
            print "R%s %s" % (key,str( mem2[key]))

if __name__ == "__main__":
    main();




